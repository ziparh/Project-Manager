import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole
from enums.task import TaskStatus, TaskPriority
from enums.project_task import ProjectTaskType

from tests.factories.models import ProjectModelFactory, ProjectTaskModelFactory


@pytest.mark.integration
class TestUpdateProjectTask:
    """Tests for PATCH /projects/{project_id}/tasks/{task_id} endpoint"""

    async def test_with_all_data(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
        other_user,
    ):
        member = ProjectMemberModel(
            user_id=other_user.id, project_id=test_project.id, role=ProjectRole.MEMBER
        )
        db_session.add(member)
        await db_session.commit()

        deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        update_data = {
            "title": "New title",
            "description": "New description",
            "deadline": deadline,
            "status": TaskStatus.IN_PROGRESS.value,
            "priority": TaskPriority.CRITICAL.value,
            "assignee_id": other_user.id,
        }

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project_task.id
        assert resp_data["title"] == update_data["title"]
        assert resp_data["description"] == update_data["description"]
        assert resp_data["deadline"].replace("Z", "+00:00") == update_data["deadline"]
        assert resp_data["status"] == update_data["status"]
        assert resp_data["priority"] == update_data["priority"]
        assert resp_data["assignee"]["id"] == update_data["assignee_id"]

        await db_session.refresh(test_project_task)

        assert test_project_task.title == update_data["title"]
        assert test_project_task.description == update_data["description"]
        assert test_project_task.deadline.isoformat() == update_data["deadline"]
        assert test_project_task.status == TaskStatus.IN_PROGRESS
        assert test_project_task.priority == TaskPriority.CRITICAL
        assert test_project_task.assignee_id == other_user.id

    @pytest.mark.parametrize(
        "update_data, changed_field",
        [
            ({"title": "New title"}, "title"),
            ({"description": "New description"}, "description"),
            ({"status": TaskStatus.DONE.value}, "status"),
            ({"priority": TaskPriority.LOW.value}, "priority"),
        ],
    )
    async def test_with_partial_data(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
        update_data,
        changed_field,
    ):
        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project_task.id
        assert resp_data[changed_field] == update_data[changed_field]

        await db_session.refresh(test_project_task)

        db_field = getattr(test_project_task, changed_field)

        if hasattr(db_field, "value"):  # For enums
            assert db_field.value == update_data[changed_field]
        else:
            assert db_field == update_data[changed_field]

    async def test_update_assignee_on_default_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user,
        other_user,
    ):
        member = ProjectMemberModel(
            user_id=other_user.id, project_id=test_project.id, role=ProjectRole.MEMBER
        )
        db_session.add(member)
        await db_session.commit()

        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            created_by_id=test_user.id,
            type=ProjectTaskType.DEFAULT,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
        )

        update_data = {"assignee_id": other_user.id}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["assignee"]["id"] == other_user.id

    async def test_cannot_add_assignee_to_open_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user,
        other_user,
    ):
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            created_by_id=test_user.id,
            type=ProjectTaskType.OPEN,
            assignee_id=None,
        )

        update_data = {"assignee_id": other_user.id}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}",
            json=update_data,
        )

        assert response.status_code == 400

    async def test_as_owner(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
    ):
        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["title"] == update_data["title"]

    async def test_as_admin(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            assignee_id=other_user.id,
            project_id=project.id,
            created_by_id=other_user.id,
            title="Old title",
            assigned_at=datetime.now(timezone.utc),
        )

        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}/tasks/{task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["title"] == update_data["title"]

    async def test_member_cannot_update_own_task_other_fields(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=project.id,
            created_by_id=other_user.id,
            assignee_id=test_user.id,
            title="Old title",
            assigned_at=datetime.now(timezone.utc),
        )

        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}/tasks/{task.id}",
            json=update_data,
        )

        assert response.status_code == 403

    async def test_member_can_update_own_task_status(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=project.id,
            created_by_id=other_user.id,
            assignee_id=test_user.id,
            status=TaskStatus.TODO,
            assigned_at=datetime.now(timezone.utc),
        )

        update_data = {"status": TaskStatus.IN_PROGRESS.value}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}/tasks/{task.id}",
            json=update_data,
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["status"] == TaskStatus.IN_PROGRESS.value

        await db_session.refresh(task)
        assert task.status == TaskStatus.IN_PROGRESS

    async def test_member_cannot_update_other_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=project.id,
            created_by_id=other_user.id,
            assignee_id=other_user.id,
            title="Old title",
            assigned_at=datetime.now(timezone.utc),
        )

        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}/tasks/{task.id}",
            json=update_data,
        )

        assert response.status_code == 403

        await db_session.refresh(task)
        assert task.title != update_data["title"]

    async def test_assignee_not_member(
        self, authenticated_client: AsyncClient, test_project, test_project_task
    ):
        update_data = {"assignee_id": 9999}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}",
            json=update_data,
        )

        assert response.status_code == 404

    async def test_task_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/9999",
            json=update_data,
        )

        assert response.status_code == 404

    async def test_not_member_of_project(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=project.id,
            created_by_id=other_user.id,
        )

        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}/tasks/{task.id}",
            json=update_data,
        )

        assert response.status_code == 403

        await db_session.refresh(task)
        assert task.title != update_data["title"]

    async def test_without_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
    ):
        update_data = {"title": "New title"}

        response = await client.patch(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}",
            json=update_data,
        )

        assert response.status_code == 401

        await db_session.refresh(test_project_task)
        assert test_project_task.title != update_data["title"]
