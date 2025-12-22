import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from modules.personal_tasks.model import PersonalTask as PersonalTaskModel

from tests.factories.models import PersonalTaskModelFactory


@pytest.mark.integration
class TestDeletePersonalTask:
    """Tests for DELETE /personal_tasks/{task_id} endpoint"""

    async def test_success(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.delete(f"api/v1/personal_tasks/{task.id}")

        assert response.status_code == 204

        deleted_task = await db_session.get(PersonalTaskModel, task.id)
        assert deleted_task is None

    async def test_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.delete("/api/v1/personal_tasks/9999")
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

    async def test_not_found_other_user_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        task = PersonalTaskModelFactory.build(user_id=other_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.delete(
            f"/api/v1/personal_tasks/{task.id}"
        )
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

        task = await db_session.get(PersonalTaskModel, task.id)
        assert task is not None

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await client.delete(f"api/v1/personal_tasks/{task.id}")

        assert response.status_code == 401

        task = await db_session.get(PersonalTaskModel, task.id)
        assert task is not None
