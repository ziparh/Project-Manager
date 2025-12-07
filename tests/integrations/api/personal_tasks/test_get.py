import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


from tests.factories.models import UserModelFactory, PersonalTaskModelFactory


@pytest.mark.integration
class TestGetPersonalTask:
    """Tests for GET /personal_tasks/{task_id} endpoint"""

    async def test_success(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.get(f"/api/v1/personal_tasks/{task.id}")
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data["title"] == task.title

    async def test_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.get("/api/v1/personal_tasks/9999")
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

    async def test_not_found_other_task(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        other_user = UserModelFactory.build()

        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        task = PersonalTaskModelFactory.build(user_id=other_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.get(f"/api/v1/personal_tasks/{task.id}")
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await client.get(f"/api/v1/personal_tasks/{task.id}")

        assert response.status_code == 401
