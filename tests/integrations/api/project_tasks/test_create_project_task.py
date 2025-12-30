import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project_task import ProjectTaskType
from enums.task import TaskStatus, TaskPriority
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory


@pytest.mark.integration
class TestCreateProjectTask:
    """Tests for POST /projects/{project_id}/tasks endpoint"""

    async def test_with_all_data(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project,
    ):
        deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        task_data = {
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": test_user.id,
            "title": "Test Task",
            "description": "Some description",
            "deadline": deadline,
            "status": TaskStatus.TODO.value,
            "priority": TaskPriority.HIGH.value,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )
        resp_data = response.json()

        assert response.status_code == 201

        db_task = await db_session.get(ProjectTaskModel, resp_data["id"])

        assert db_task is not None
        assert resp_data["title"] == db_task.title
        assert resp_data["description"] == db_task.description
        assert resp_data["deadline"] == db_task.deadline.isoformat().replace(
            "+00:00", "Z"
        )
        assert resp_data["status"] == db_task.status.value
        assert resp_data["priority"] == db_task.priority.value
        assert resp_data["type"] == db_task.type.value
        assert resp_data["assignee"]["id"] == db_task.assignee_id
        assert resp_data["creator"]["id"] == test_user.id
        assert db_task.assigned_at is not None

    async def test_with_minimal_data(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project,
    ):
        task_data = {
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": test_user.id,
            "title": "Test Task",
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )
        resp_data = response.json()

        assert response.status_code == 201

        db_task = await db_session.get(ProjectTaskModel, resp_data["id"])

        assert db_task is not None
        assert resp_data["title"] == db_task.title
        assert db_task.description is None
        assert db_task.deadline is None
        assert db_task.status == TaskStatus.TODO  # Status by default
        assert db_task.priority == TaskPriority.MEDIUM  # Priority by default
        assert db_task.type == ProjectTaskType.DEFAULT  # Type by default
        assert db_task.assignee_id == test_user.id
        assert db_task.assigned_at is not None

    async def test_open_task_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project,
    ):
        task_data = {
            "title": "Open Task",
            "type": ProjectTaskType.OPEN.value,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )
        resp_data = response.json()

        assert response.status_code == 201

        db_task = await db_session.get(ProjectTaskModel, resp_data["id"])

        assert db_task is not None
        assert db_task.type == ProjectTaskType.OPEN
        assert db_task.assignee_id is None
        assert db_task.assigned_at is None

    @pytest.mark.parametrize(
        "invalid_data, expected_field",
        [
            ({"title": ""}, "title"),  # Empty title
            ({"title": "f" * 201}, "title"),  # Title max length is 200
            (
                {"title": "Test", "description": "f" * 1001},
                "description",
            ),  # Description max length is 1000
        ],
    )
    async def test_validation_errors(
        self,
        authenticated_client: AsyncClient,
        test_project,
        invalid_data,
        expected_field,
    ):
        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=invalid_data
        )

        assert response.status_code == 422

        errors = response.json()["detail"]
        assert any(expected_field in str(error["loc"]) for error in errors)

    async def test_cannot_add_assignee_to_open_task(
        self,
        authenticated_client: AsyncClient,
        test_project,
        test_user,
    ):
        task_data = {
            "title": "Test",
            "type": ProjectTaskType.OPEN.value,
            "assignee_id": test_user.id,
        }
        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )

        detail = response.json()["detail"]
        assert detail[0]["msg"] == "Value error, assignee_id must be None when type is 'open'"

    async def test_need_to_add_assignee_to_default_task(
        self,
        authenticated_client: AsyncClient,
        test_project,
    ):
        task_data = {"title": "Test", "type": ProjectTaskType.DEFAULT.value}

        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )

        detail = response.json()["detail"]
        assert detail[0]["msg"] == "Value error, assignee_id must be set when type is 'default'"

    async def test_assignee_not_member_of_project(
        self, authenticated_client: AsyncClient, test_project
    ):
        task_data = {
            "title": "Test Task",
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": 9999,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.OWNER])
    async def test_admin_and_owner_can_create(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        role,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=role)],
        )

        task_data = {
            "title": "Test Task",
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": test_user.id,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{project.id}/tasks", json=task_data
        )

        assert response.status_code == 201
        assert response.json()["title"] == "Test Task"

    async def test_member_cannot_create(
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

        task_data = {
            "title": "Test Task",
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": test_user.id,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{project.id}/tasks", json=task_data
        )

        assert response.status_code == 403

    async def test_not_member_of_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )

        task_data = {
            "title": "Test Task",
            "type": ProjectTaskType.DEFAULT.value,
            "assignee_id": other_user.id,
        }

        response = await authenticated_client.post(
            f"/api/v1/projects/{project.id}/tasks", json=task_data
        )

        assert response.status_code == 403

    async def test_without_token(self, client: AsyncClient, test_project):
        task_data = {"title": "Test Task"}

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/tasks", json=task_data
        )

        assert response.status_code == 401
