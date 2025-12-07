import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from modules.personal_tasks.model import PersonalTask as PersonalTaskModel
from enums.task import TaskStatus, TaskPriority


@pytest.mark.integration
class TestCreatePersonalTask:
    """Tests for POST /personal_tasks endpoint"""

    async def test_with_all_data(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        task_data = {
            "title": "Test Task",
            "description": "Some description",
            "deadline": deadline,
            "priority": TaskPriority.CRITICAL.value,
            "status": TaskStatus.IN_PROGRESS.value,
        }

        response = await authenticated_client.post(
            "api/v1/personal_tasks", json=task_data
        )
        resp_data = response.json()

        db_task = await db_session.get(PersonalTaskModel, resp_data["id"])

        assert response.status_code == 201
        assert resp_data["title"] == db_task.title
        assert resp_data["description"] == db_task.description
        assert resp_data["deadline"] == db_task.deadline.isoformat().replace(
            "+00:00", "Z"
        )
        assert resp_data["priority"] == db_task.priority.value
        assert resp_data["status"] == db_task.status.value

    async def test_with_minimal_data(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task_data = {"title": "Test Task"}

        response = await authenticated_client.post(
            "api/v1/personal_tasks", json=task_data
        )
        resp_data = response.json()

        db_task = await db_session.get(PersonalTaskModel, resp_data["id"])

        assert response.status_code == 201
        assert resp_data["title"] == db_task.title
        assert db_task.description is None
        assert db_task.deadline is None
        assert db_task.priority == TaskPriority.MEDIUM  # Priority by default
        assert db_task.status == TaskStatus.TODO  # Status by default

    @pytest.mark.parametrize(
        "invalid_data, expected_field",
        [
            ({"title": ""}, "title"),
            ({"title": "f" * 201}, "title"),  # Title max length is 200
            (
                {
                    "title": "Task",
                    "description": "f" * 1001,  # Description max length is 1000
                },
                "description",
            ),
        ],
    )
    async def test_validation_errors(
        self, authenticated_client: AsyncClient, invalid_data: dict, expected_field: str
    ):
        response = await authenticated_client.post(
            "api/v1/personal_tasks", json=invalid_data
        )
        assert response.status_code == 422

        errors = response.json()["detail"]
        assert any(expected_field in str(error["loc"]) for error in errors)

    async def test_without_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/personal_tasks", json={"title": "Test title"}
        )

        assert response.status_code == 401
