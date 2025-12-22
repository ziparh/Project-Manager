import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from enums.task import TaskStatus, TaskPriority

from tests.factories.models import PersonalTaskModelFactory


@pytest.mark.integration
class TestGetListOfPersonalTasks:
    """Tests for GET /personal_tasks endpoint"""

    async def test_return_user_tasks(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        user_tasks = [
            PersonalTaskModelFactory.build(user_id=test_user.id, title=f"Task {i}")
            for i in range(3)
        ]
        other_user_tasks = [
            PersonalTaskModelFactory.build(
                user_id=other_user.id, title=f"Other task {i}"
            )
            for i in range(2)
        ]

        db_session.add_all(user_tasks + other_user_tasks)
        await db_session.commit()

        response = await authenticated_client.get("/api/v1/personal_tasks")
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 3

        titles = [item["title"] for item in resp_data["items"]]
        assert "Task 0" in titles
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Other task" not in titles

    async def test_filters_status(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        params = {"status": TaskStatus.DONE.value}
        task_todo = PersonalTaskModelFactory.build(
            user_id=test_user.id, status=TaskStatus.TODO
        )
        task_done = PersonalTaskModelFactory.build(
            user_id=test_user.id, status=TaskStatus.DONE
        )

        db_session.add_all([task_todo, task_done])
        await db_session.commit()

        response = await authenticated_client.get(
            "/api/v1/personal_tasks", params=params
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 1
        assert len(resp_data["items"]) == 1
        assert resp_data["items"][0]["status"] == TaskStatus.DONE.value

    async def test_filters_priority(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        params = {"priority": TaskPriority.CRITICAL.value}
        task_high = PersonalTaskModelFactory.build(
            user_id=test_user.id, priority=TaskPriority.HIGH
        )
        task_critical = PersonalTaskModelFactory.build(
            user_id=test_user.id, priority=TaskPriority.CRITICAL
        )

        db_session.add_all([task_high, task_critical])
        await db_session.commit()

        response = await authenticated_client.get(
            "/api/v1/personal_tasks", params=params
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 1
        assert len(resp_data["items"]) == 1
        assert resp_data["items"][0]["priority"] == TaskPriority.CRITICAL.value

    async def test_search(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        params = {"search": "dinner"}

        meeting_task = PersonalTaskModelFactory.build(
            user_id=test_user.id, title="Important meeting", description="Business"
        )
        dinner_task = PersonalTaskModelFactory.build(
            user_id=test_user.id, title="Family dinner", description="Fish"
        )
        products_task = PersonalTaskModelFactory.build(
            user_id=test_user.id, title="Buy products", description="Fish for dinner"
        )

        db_session.add_all([meeting_task, dinner_task, products_task])
        await db_session.commit()

        response = await authenticated_client.get(
            "/api/v1/personal_tasks", params=params
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert len(resp_data["items"]) == 2

    async def test_pagination(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        params = {"page": 3, "size": 2}
        tasks = [PersonalTaskModelFactory.build(user_id=test_user.id) for _ in range(5)]

        db_session.add_all(tasks)
        await db_session.commit()

        response = await authenticated_client.get(
            "/api/v1/personal_tasks", params=params
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert len(resp_data["items"]) == 1
        assert resp_data["pagination"]["total"] == 5
        assert resp_data["pagination"]["page"] == 3

    async def test_without_token(self, client: AsyncClient):
        response = await client.get("/api/v1/personal_tasks")

        assert response.status_code == 401
