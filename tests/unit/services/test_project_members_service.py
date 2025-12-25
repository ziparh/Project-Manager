import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status

from modules.project_members import (
    repository as members_repository,
    service as member_service,
    schemas as members_schemas,
)
from modules.users import repository as users_repository
from common import schemas as common_schemas
from core.security.permissions import PermissionChecker
from enums.project import ProjectRole, ProjectPermission

from tests.factories.models import (
    ProjectMemberModelFactory,
    ProjectModelFactory,
    UserModelFactory,
)
from tests.factories.schemas import ProjectMemberAddFactory, ProjectMemberPatchFactory


@pytest.fixture
def mock_member_repo():
    """Mock project member repository"""
    return AsyncMock(spec=members_repository.ProjectMemberRepository)


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return AsyncMock(spec=users_repository.UserRepository)


@pytest.fixture
def service(mock_member_repo, mock_user_repo):
    """Project member service with mocked project member and user repository"""
    return member_service.ProjectMemberService(
        member_repo=mock_member_repo, user_repo=mock_user_repo
    )


@pytest.mark.unit
class TestGetAll:
    async def test_pagination_response(self, service, mock_member_repo):
        project = ProjectMemberModelFactory.build()
        members = [ProjectMemberModelFactory() for _ in range(10)]

        mock_member_repo.get_all.return_value = [members, 10]

        filters = members_schemas.ProjectMemberFilterParams()
        sorting = members_schemas.ProjectMemberSortingParams(sort_by="joined_at")
        pagination = common_schemas.BasePaginationParams(page=2, size=4)

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
        assert result.pagination.size == 4
        assert result.pagination.pages == 3
        assert result.pagination.has_next
        assert result.pagination.has_previous

    async def test_call_repository_with_correct_params(self, service, mock_member_repo):
        project = ProjectMemberModelFactory.build()

        mock_member_repo.get_all.return_value = [[], 0]

        filters = members_schemas.ProjectMemberFilterParams(role=ProjectRole.ADMIN)
        sorting = members_schemas.ProjectMemberSortingParams(
            sort_by="role", order="desc"
        )
        pagination = common_schemas.BasePaginationParams(page=3, size=10)

        await service.get_all(
            project_id=project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        mock_member_repo.get_all.assert_called_once()

        kwargs = mock_member_repo.get_all.call_args.kwargs

        assert kwargs["project_id"] == project.id
        assert kwargs["filters"].role == filters.role
        assert kwargs["sorting"].sort_by == sorting.sort_by
        assert kwargs["sorting"].order == sorting.order
        assert kwargs["pagination"].size == 10
        assert kwargs["pagination"].offset == 20

    async def test_with_empty_results(self, service, mock_member_repo):
        project = ProjectModelFactory.build()

        mock_member_repo.get_all.return_value = [[], 0]

        filters = members_schemas.ProjectMemberFilterParams()
        sorting = members_schemas.ProjectMemberSortingParams(sort_by="joined_at")
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
class TestAdd:
    @patch.object(PermissionChecker, "validate_role_assignment")
    async def test_success(
        self, mock_assignment_validate, service, mock_member_repo, mock_user_repo
    ):
        user = UserModelFactory.build()
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        data_to_add = ProjectMemberAddFactory.build()

        mock_assignment_validate.return_value = None
        mock_user_repo.get_by_id.return_value = user
        mock_member_repo.get_by_user_id_and_project_id.return_value = None
        mock_member_repo.create.return_value = membership

        result = await service.add(
            project_id=project.id,
            actor=actor,
            data=data_to_add,
        )

        assert result == membership
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=data_to_add.role
        )
        mock_user_repo.get_by_id.assert_called_once_with(data_to_add.user_id)
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=data_to_add.user_id, project_id=project.id
        )
        mock_member_repo.create.assert_called_once()

    @patch.object(PermissionChecker, "validate_role_assignment")
    async def test_cannot_assign_role(
        self, mock_assignment_validate, service, mock_member_repo, mock_user_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        data_to_add = ProjectMemberAddFactory.build()
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{actor.role} cannot assign {data_to_add.role} role.",
        )

        mock_assignment_validate.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.add(
                project_id=project.id,
                actor=actor,
                data=data_to_add,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=data_to_add.role
        )
        mock_user_repo.get_by_id.assert_not_called()
        mock_member_repo.get_by_user_id_and_project_id.assert_not_called()
        mock_member_repo.create.assert_not_called()

    @patch.object(PermissionChecker, "validate_role_assignment")
    async def test_user_not_found(
        self, mock_assignment_validate, service, mock_member_repo, mock_user_repo
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        data_to_add = ProjectMemberAddFactory.build()

        mock_assignment_validate.return_value = None
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.add(
                project_id=project.id,
                actor=actor,
                data=data_to_add,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found."
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=data_to_add.role
        )
        mock_user_repo.get_by_id.assert_called_once_with(data_to_add.user_id)
        mock_member_repo.get_by_user_id_and_project_id.assert_not_called()
        mock_member_repo.create.assert_not_called()

    @patch.object(PermissionChecker, "validate_role_assignment")
    async def test_conflict_membership(
        self, mock_assignment_validate, service, mock_member_repo, mock_user_repo
    ):
        user = UserModelFactory.build()
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        data_to_add = ProjectMemberAddFactory.build()

        mock_assignment_validate.return_value = None
        mock_user_repo.get_by_id.return_value = user
        mock_member_repo.get_by_user_id_and_project_id.return_value = membership

        with pytest.raises(HTTPException) as exc_info:
            await service.add(
                project_id=project.id,
                actor=actor,
                data=data_to_add,
            )

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert exc_info.value.detail == "User is already a project member."
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=data_to_add.role
        )
        mock_user_repo.get_by_id.assert_called_once_with(data_to_add.user_id)
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=data_to_add.user_id, project_id=project.id
        )
        mock_member_repo.create.assert_not_called()


@pytest.mark.unit
class TestUpdate:
    @patch.object(PermissionChecker, "validate_role_assignment")
    @patch.object(PermissionChecker, "validate_member_operation")
    async def test_success(
        self,
        mock_operation_validate,
        mock_assignment_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        update_data = ProjectMemberPatchFactory.build()
        updated_membership = ProjectMemberModelFactory.build(**update_data.model_dump())

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_operation_validate.return_value = None
        mock_assignment_validate.return_value = None
        mock_member_repo.update_by_membership.return_value = updated_membership

        result = await service.update(
            project_id=project.id,
            user_id=membership.user_id,
            actor=actor,
            update_data=update_data,
        )

        assert result == updated_membership
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_operation_validate.assert_called_once_with(
            actor_role=actor.role, target_role=membership.role, operation="update"
        )
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=update_data.role
        )
        mock_member_repo.update_by_membership.assert_called_once()

    @patch.object(PermissionChecker, "validate_role_assignment")
    @patch.object(PermissionChecker, "validate_member_operation")
    async def test_with_no_data(
        self,
        mock_operation_validate,
        mock_assignment_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        update_data = members_schemas.ProjectMemberPatch()

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "No data to update."
        mock_member_repo.get_by_user_id_and_project_id.assert_not_called()
        mock_operation_validate.assert_not_called()
        mock_assignment_validate.assert_not_called()
        mock_member_repo.update_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_role_assignment")
    @patch.object(PermissionChecker, "validate_member_operation")
    async def test_membership_not_found(
        self,
        mock_operation_validate,
        mock_assignment_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        update_data = ProjectMemberPatchFactory.build()

        mock_member_repo.get_by_user_id_and_project_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                user_id=9999,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Member not found."
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=9999, project_id=project.id
        )
        mock_operation_validate.assert_not_called()
        mock_assignment_validate.assert_not_called()
        mock_member_repo.update_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_role_assignment")
    @patch.object(PermissionChecker, "validate_member_operation")
    async def test_cannot_modify(
        self,
        mock_operation_validate,
        mock_assignment_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        update_data = ProjectMemberPatchFactory.build()
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{actor.role} cannot update {membership.role}.",
        )

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_operation_validate.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_operation_validate.assert_called_once_with(
            actor_role=actor.role, target_role=membership.role, operation="update"
        )
        mock_assignment_validate.assert_not_called()
        mock_member_repo.update_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_role_assignment")
    @patch.object(PermissionChecker, "validate_member_operation")
    async def test_cannot_assign_role(
        self,
        mock_operation_validate,
        mock_assignment_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()
        membership = ProjectMemberModelFactory.build()
        update_data = ProjectMemberPatchFactory.build()
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{actor.role} cannot assign {update_data.role} role.",
        )

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_operation_validate.return_value = None
        mock_assignment_validate.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.update(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
                update_data=update_data,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_operation_validate.assert_called_once_with(
            actor_role=actor.role, target_role=membership.role, operation="update"
        )
        mock_assignment_validate.assert_called_once_with(
            actor_role=actor.role, new_role=update_data.role
        )
        mock_member_repo.update_by_membership.assert_not_called()


@pytest.mark.unit
class TestDelete:
    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_actor_delete_other_member_success(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.ADMIN)
        membership = ProjectMemberModelFactory.build(user_id=2, role=ProjectRole.MEMBER)

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_require_permission.return_value = None
        mock_operation_validate.return_value = None

        await service.delete(
            project_id=project.id,
            user_id=membership.user_id,
            actor=actor,
        )

        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_operation_validate.assert_called_once_with(
            actor_role=actor.role, target_role=membership.role, operation="remove"
        )
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.REMOVE_MEMBERS
        )
        mock_member_repo.delete_by_membership.assert_called_once()

    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_user_delete_themselves_success(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        membership = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership

        await service.delete(
            project_id=project.id,
            user_id=membership.user_id,
            actor=actor,
        )

        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_require_permission.assert_not_called()
        mock_operation_validate.assert_not_called()
        mock_member_repo.delete_by_membership.assert_called_once()

    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_membership_not_found(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build()

        mock_member_repo.get_by_user_id_and_project_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.delete(
                project_id=project.id,
                user_id=9999,
                actor=actor,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Member not found."
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=9999, project_id=project.id
        )
        mock_require_permission.assert_not_called()
        mock_operation_validate.assert_not_called()
        mock_member_repo.delete_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_owner_cannot_delete_themselves(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.OWNER)
        membership = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.OWNER)

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership

        with pytest.raises(HTTPException) as exc_info:
            await service.delete(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Owner cannot remove themselves."
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_require_permission.assert_not_called()
        mock_operation_validate.assert_not_called()
        mock_member_repo.delete_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_have_no_required_permission(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        membership = ProjectMemberModelFactory.build(user_id=2, role=ProjectRole.ADMIN)
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have such permission.",
        )

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_require_permission.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.delete(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.REMOVE_MEMBERS
        )
        mock_operation_validate.assert_not_called()
        mock_member_repo.delete_by_membership.assert_not_called()

    @patch.object(PermissionChecker, "validate_member_operation")
    @patch.object(PermissionChecker, "require_permission")
    async def test_cannot_modify(
        self,
        mock_require_permission,
        mock_operation_validate,
        service,
        mock_member_repo,
    ):
        project = ProjectModelFactory.build()
        actor = ProjectMemberModelFactory.build(user_id=1, role=ProjectRole.MEMBER)
        membership = ProjectMemberModelFactory.build(user_id=2, role=ProjectRole.ADMIN)
        permission_exc = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{actor.role} cannot remove {membership.role}.",
        )

        mock_member_repo.get_by_user_id_and_project_id.return_value = membership
        mock_require_permission.return_value = None
        mock_operation_validate.side_effect = permission_exc

        with pytest.raises(HTTPException) as exc_info:
            await service.delete(
                project_id=project.id,
                user_id=membership.user_id,
                actor=actor,
            )

        assert exc_info.value.status_code == permission_exc.status_code
        assert exc_info.value.detail == permission_exc.detail
        mock_member_repo.get_by_user_id_and_project_id.assert_called_once_with(
            user_id=membership.user_id, project_id=project.id
        )
        mock_require_permission.assert_called_once_with(
            role=actor.role, permission=ProjectPermission.REMOVE_MEMBERS
        )
        mock_operation_validate.assert_called_once_with(
            actor_role=actor.role, target_role=membership.role, operation="remove"
        )
        mock_member_repo.delete_by_membership.assert_not_called()
