import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from datetime import datetime

from modules.project_tasks import (
    repository as tasks_repository,
    service as task_service,
    schemas as tasks_schemas,
)
from modules.project_members import repository as members_repository
from common import schemas as common_schemas
from core.security.permissions import PermissionChecker
from enums.project_task import ProjectTaskType
from enums.project import ProjectRole, ProjectPermission
from enums.task import TaskStatus

from tests.factories.models import (
    ProjectTaskModelFactory,
    ProjectMemberModelFactory,
    ProjectModelFactory,
)
from tests.factories.schemas import (
    ProjectTaskCreateFactory,
    ProjectTaskPatchFactory,
)


@pytest.fixture
def mock_repo():
    """Mock project task repository"""
    return AsyncMock(spec=tasks_repository.ProjectTaskRepository)


@pytest.fixture
def mock_member_repo():
    """Mock project member repository"""
    return AsyncMock(spec=members_repository.ProjectMemberRepository)


@pytest.fixture
def service(mock_repo, mock_member_repo):
    """Project task service with mocked repositories"""
    return task_service.ProjectTaskService(repo=mock_repo, member_repo=mock_member_repo)


@pytest.mark.unit
class TestGetAll:
    async def test_pagination_response(self, service, mock_repo):
        project = ProjectModelFactory.build()
        tasks = [ProjectTaskModelFactory.build() for _ in range(10)]

        mock_repo.get_all.return_value = [tasks, 10]

        filters = tasks_schemas.ProjectTasksFiltersParams()
        sorting = tasks_schemas.ProjectTasksSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=2, size=5)

        result = await service.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert isinstance(result, common_schemas.BasePaginationResponse)
        assert len(result.items) == 10
        assert result.pagination.total == 10
        assert result.pagination.page == 2
        assert result.pagination.size == 5
        assert result.pagination.pages == 2
        assert not result.pagination.has_next
        assert result.pagination.has_previous

    async def test_call_repository_with_correct_params(self, service, mock_repo):
        project = ProjectModelFactory.build()

        mock_repo.get_all.return_value = [[], 0]

        filters = tasks_schemas.ProjectTasksFiltersParams(status=TaskStatus.IN_PROGRESS)
        sorting = tasks_schemas.ProjectTasksSortingParams(
            sort_by="priority", order="desc"
        )
        pagination = common_schemas.BasePaginationParams(page=3, size=10)

        await service.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        mock_repo.get_all.assert_called_once()

        kwargs = mock_repo.get_all.call_args.kwargs

        assert kwargs["project_id"] == project.id
        assert kwargs["filters"].status == filters.status
        assert kwargs["sorting"].sort_by == sorting.sort_by
        assert kwargs["sorting"].order == sorting.order
        assert kwargs["pagination"].size == 10
        assert kwargs["pagination"].offset == 20

    async def test_with_empty_results(self, service, mock_repo):
        project = ProjectModelFactory.build()

        mock_repo.get_all.return_value = [[], 0]

        filters = tasks_schemas.ProjectTasksFiltersParams()
        sorting = tasks_schemas.ProjectTasksSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=1, size=10)

        result = await service.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert len(result.items) == 0
        assert result.pagination.total == 0
        assert result.pagination.page == 1
        assert result.pagination.size == 10
        assert result.pagination.pages == 1
        assert not result.pagination.has_next
        assert not result.pagination.has_previous


@pytest.mark.unit
class TestCreate:
    async def test_success_with_open_task(self, service, mock_repo):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        task_data = ProjectTaskCreateFactory.build(
            type=ProjectTaskType.OPEN, assignee_id=None
        )
        created_task = ProjectTaskModelFactory.build()

        mock_repo.create.return_value = created_task

        result = await service.create(
            project_id=project.id,
            actor=actor,
            task_data=task_data,
        )

        assert result == created_task
        mock_repo.create.assert_called_once()

        kwargs = mock_repo.create.call_args.kwargs
        assert kwargs["project_id"] == project.id
        assert kwargs["created_by_id"] == actor.user_id
        assert "assigned_at" not in kwargs["data"]

    async def test_success_with_default_task(
        self, service, mock_repo, mock_member_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        assignee = ProjectMemberModelFactory.build(user_id=123)
        task_data = ProjectTaskCreateFactory.build(
            type=ProjectTaskType.DEFAULT,
            assignee_id=assignee.user_id,
        )
        created_task = ProjectTaskModelFactory.build()

        mock_member_repo.get_by_user_id_and_project_id.return_value = assignee
        mock_repo.create.return_value = created_task

        result = await service.create(
            project_id=project.id,
            actor=actor,
            task_data=task_data,
        )

        assert result == created_task
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            project_id=project.id, user_id=task_data.assignee_id
        )
        mock_repo.create.assert_called_once()

        kwargs = mock_repo.create.call_args.kwargs

        assert kwargs["data"]["assignee_id"] == assignee.user_id
        assert "assigned_at" in kwargs["data"]
        assert isinstance(kwargs["data"]["assigned_at"], datetime)

    async def test_assignee_not_member_returns_404(
        self, service, mock_repo, mock_member_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        task_data = ProjectTaskCreateFactory.build(
            type=ProjectTaskType.DEFAULT,
            assignee_id=999,
        )

        mock_member_repo.get_by_user_id_and_project_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.create(
                project_id=project.id,
                actor=actor,
                task_data=task_data,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found."
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            project_id=project.id, user_id=task_data.assignee_id
        )
        mock_repo.create.assert_not_called()


@pytest.mark.unit
class TestUpdate:
    @patch.object(PermissionChecker, "require_permission")
    async def test_success_as_actor_with_permission(
        self, mock_require_permission, service, mock_repo, mock_member_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.ADMIN)
        task = ProjectTaskModelFactory.build(type=ProjectTaskType.DEFAULT, assignee_id=2)
        update_data = ProjectTaskPatchFactory.build(title="Updated Title")
        updated_task = ProjectTaskModelFactory.build()

        mock_require_permission.return_value = None
        mock_repo.update_by_task.return_value = updated_task

        result = await service.update(
            project_id=project.id,
            task=task,
            actor=actor,
            update_data=update_data,
        )

        assert result == updated_task
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.UPDATE_TASKS
        )
        mock_repo.update_by_task.assert_called_once()

    @patch.object(PermissionChecker, "require_permission")
    async def test_success_own_task_status(
        self, mock_require_permission, service, mock_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        task = ProjectTaskModelFactory.build(assignee_id=1)
        update_data = tasks_schemas.ProjectTaskPatch(status=TaskStatus.DONE)
        updated_task = ProjectTaskModelFactory.build()

        mock_require_permission.return_value = None
        mock_repo.update_by_task.return_value = updated_task

        result = await service.update(
            project_id=project.id,
            task=task,
            actor=actor,
            update_data=update_data,
        )

        assert result == updated_task
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.UPDATE_OWN_TASK_STATUS
        )
        mock_repo.update_by_task.assert_called_once()

    @patch.object(PermissionChecker, "require_permission")
    async def test_with_no_data(
        self, mock_require_permission, service, mock_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        task = ProjectTaskModelFactory.build()
        update_data = tasks_schemas.ProjectTaskPatch()

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                task=task,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "No data to update."
        mock_require_permission.assert_not_called()
        mock_repo.update_by_task.assert_not_called()

    @patch.object(PermissionChecker, "require_permission")
    async def test_member_cannot_update_other_task(
        self, mock_require_permission, service, mock_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        task = ProjectTaskModelFactory.build(assignee_id=2)
        update_data = ProjectTaskPatchFactory.build(title="Test")
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have such permission.",
        )

        mock_require_permission.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                task=task,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.UPDATE_TASKS
        )
        mock_repo.update_by_task.assert_not_called()

    @patch.object(PermissionChecker, "require_permission")
    async def test_success_update_assignee_on_default_task(
        self, mock_require_permission, service, mock_repo, mock_member_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(role=ProjectRole.ADMIN)
        task = ProjectTaskModelFactory.build(type=ProjectTaskType.DEFAULT)
        new_assignee = ProjectMemberModelFactory.build()
        update_data = tasks_schemas.ProjectTaskPatch(assignee_id=new_assignee.user_id)
        updated_task = ProjectTaskModelFactory.build()

        mock_require_permission.return_value = None
        mock_member_repo.get_by_user_id_and_project_id.return_value = new_assignee
        mock_repo.update_by_task.return_value = updated_task

        result = await service.update(
            project_id=project.id,
            task=task,
            actor=actor,
            update_data=update_data,
        )

        assert result == updated_task
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            project_id=project.id, user_id=new_assignee.user_id
        )
        mock_repo.update_by_task.assert_called_once()

    @patch.object(PermissionChecker, "require_permission")
    async def test_assignee_not_member(
        self, mock_require_permission, service, mock_repo, mock_member_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(role=ProjectRole.ADMIN)
        task = ProjectTaskModelFactory.build(type=ProjectTaskType.DEFAULT)
        update_data = tasks_schemas.ProjectTaskPatch(assignee_id=999)

        mock_require_permission.return_value = None
        mock_member_repo.get_by_user_id_and_project_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                task=task,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found."
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            project_id=project.id, user_id=999
        )
        mock_repo.update_by_task.assert_not_called()

    @patch.object(PermissionChecker, "require_permission")
    async def test_cannot_add_assignee_to_open_task(
        self, mock_require_permission, service, mock_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(role=ProjectRole.ADMIN)
        task = ProjectTaskModelFactory.build(type=ProjectTaskType.OPEN)
        update_data = tasks_schemas.ProjectTaskPatch(assignee_id=123)

        mock_require_permission.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                task=task,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "You cannot add assignee to open task."
        mock_repo.update_by_task.assert_not_called()


@pytest.mark.unit
class TestDelete:
    async def test_success(self, service, mock_repo):
        task = ProjectTaskModelFactory.build()

        await service.delete(task=task)

        mock_repo.delete_by_task.assert_called_once_with(task)


@pytest.mark.unit
class TestAssign:
    async def test_success(self, service, mock_repo):
        actor = ProjectMemberModelFactory.build(user_id=1)
        task = ProjectTaskModelFactory.build(
            type=ProjectTaskType.OPEN,
            assignee_id=None,
        )
        assigned_task = ProjectTaskModelFactory.build(assignee_id=actor.user_id)

        mock_repo.update_by_task.return_value = assigned_task

        result = await service.assign(task=task, actor=actor)

        assert result == assigned_task
        mock_repo.update_by_task.assert_called_once()

        kwargs = mock_repo.update_by_task.call_args.kwargs
        assert kwargs["task"] == task
        assert kwargs["data"]["assignee_id"] == actor.user_id
        assert "assigned_at" in kwargs["data"]
        assert isinstance(kwargs["data"]["assigned_at"], datetime)

    async def test_task_already_assigned(self, service, mock_repo):
        actor = ProjectMemberModelFactory.build(user_id=1)
        task = ProjectTaskModelFactory.build(
            type=ProjectTaskType.OPEN,
            assignee_id=2,  # Already assigned
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.assign(task=task, actor=actor)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Task is already assigned."
        mock_repo.update_by_task.assert_not_called()


@pytest.mark.unit
class TestUnassign:
    async def test_success_own_task(self, service, mock_repo):
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        task = ProjectTaskModelFactory.build(
            assignee_id=1,  # Own task
        )
        unassigned_task = ProjectTaskModelFactory.build(assignee_id=None)

        mock_repo.update_by_task.return_value = unassigned_task

        result = await service.unassign(task=task, actor=actor)

        assert result == unassigned_task
        mock_repo.update_by_task.assert_called_once()

        kwargs = mock_repo.update_by_task.call_args.kwargs
        assert kwargs["task"] == task
        assert kwargs["data"]["assignee_id"] is None
        assert kwargs["data"]["assigned_at"] is None

    @patch.object(PermissionChecker, "has_permission")
    async def test_success_admin_unassigns_other_task(
        self, mock_has_permission, service, mock_repo
    ):
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.ADMIN)
        task = ProjectTaskModelFactory.build(
            assignee_id=2,  # Other's task
        )
        unassigned_task = ProjectTaskModelFactory.build(assignee_id=None)

        mock_has_permission.return_value = True
        mock_repo.update_by_task.return_value = unassigned_task

        result = await service.unassign(task=task, actor=actor)

        assert result == unassigned_task
        mock_has_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.UPDATE_TASKS
        )
        mock_repo.update_by_task.assert_called_once()

    async def test_task_not_assigned(self, service, mock_repo):
        actor = ProjectMemberModelFactory.build()
        task = ProjectTaskModelFactory.build(
            assignee_id=None,  # Not assigned
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.unassign(task=task, actor=actor)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Task is not assigned."
        mock_repo.update_by_task.assert_not_called()

    @patch.object(PermissionChecker, "has_permission")
    async def test_member_cannot_unassign_other_task(
        self, mock_has_permission, service, mock_repo
    ):
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        task = ProjectTaskModelFactory.build(
            assignee_id=2,  # Other's task
        )

        mock_has_permission.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await service.unassign(task=task, actor=actor)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "You can unassign only your own tasks."
        mock_has_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.UPDATE_TASKS
        )
        mock_repo.update_by_task.assert_not_called()
