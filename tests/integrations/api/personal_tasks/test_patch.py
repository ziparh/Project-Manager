import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from modules.personal_tasks import schemas
from enums.task import TaskStatus, TaskPriority

from tests.factories.models import PersonalTaskModelFactory, UserModelFactory


@pytest.mark.integration
class TestPatchPersonalTask:
    """Tests for PATCH /personal_tasks/{task_id} endpoint"""

    async def test_all_success(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            title="Old title",
            description="Some old description",
            deadline=datetime.now(timezone.utc) + timedelta(days=1),
            priority=TaskPriority.LOW,
            status=TaskStatus.TODO,
        )
        update_data = schemas.PersonalTaskPatch(
            title="New title",
            description="Some new description",
            deadline=datetime.now(timezone.utc) + timedelta(days=2),
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
        )

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.patch(
            f"/api/v1/personal_tasks/{task.id}",
            json=update_data.model_dump(mode="json"),
        )
        resp_data = response.json()
        expected_deadline = update_data.deadline

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data["title"] == update_data.title
        assert resp_data["description"] == update_data.description
        assert resp_data["deadline"] == expected_deadline.isoformat().replace(
            "+00:00", "Z"
        )
        assert resp_data["priority"] == update_data.priority.value
        assert resp_data["status"] == update_data.status.value

        await db_session.refresh(task)

        assert task.title == update_data.title
        assert task.description == update_data.description
        assert task.deadline == update_data.deadline
        assert task.priority == update_data.priority
        assert task.status == update_data.status

    @pytest.mark.parametrize(
        "update_data, changed_field",
        [
            (schemas.PersonalTaskPatch(title="New title"), "title"),
            (schemas.PersonalTaskPatch(description="New desc"), "description"),
            (schemas.PersonalTaskPatch(priority=TaskPriority.HIGH), "priority"),
            (schemas.PersonalTaskPatch(status=TaskStatus.IN_PROGRESS), "status"),
        ],
    )
    async def test_partial_success(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        update_data: schemas.PersonalTaskPatch,
        changed_field: str,
        test_user,
    ):
        task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            title="Old title",
            description="Old desc",
            priority=TaskPriority.LOW,
            status=TaskStatus.TODO,
        )
        update_dict = update_data.model_dump(exclude_unset=True, mode="json")

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.patch(
            f"/api/v1/personal_tasks/{task.id}", json=update_dict
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data[changed_field] == update_dict[changed_field]

        await db_session.refresh(task)

        db_field = getattr(task, changed_field)

        if hasattr(db_field, "value"):  # For enums
            assert db_field.value == update_dict[changed_field]
        else:
            assert db_field == update_dict[changed_field]

    async def test_deadline_success(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=datetime.now(timezone.utc) + timedelta(days=1),
        )
        update_data = schemas.PersonalTaskPatch(
            deadline=datetime.now(timezone.utc) + timedelta(days=2),
        )
        update_dict = update_data.model_dump(exclude_unset=True, mode="json")

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.patch(
            f"/api/v1/personal_tasks/{task.id}", json=update_dict
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data["deadline"] == update_dict["deadline"]

        await db_session.refresh(task)

        assert task.deadline == update_data.deadline

    async def test_not_found(self, authenticated_client: AsyncClient):
        response = await authenticated_client.patch(
            "/api/v1/personal_tasks/9999", json={"title": "Some other title"}
        )
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

    async def test_not_found_other_user_task(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        other_user = UserModelFactory.build()

        db_session.add(other_user)
        await db_session.commit()

        task = PersonalTaskModelFactory.build(user_id=other_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await authenticated_client.patch(
            f"/api/v1/personal_tasks/{task.id}",
            json={"title": "Some other title"},
        )
        resp_data = response.json()

        assert response.status_code == 404
        assert "not found" in resp_data["detail"].lower()

        await db_session.refresh(task)
        assert task.title != "Some other title"

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_user
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/personal_tasks/{task.id}", json={"title": "Some other title"}
        )

        assert response.status_code == 401

        await db_session.refresh(task)

        assert task.title != "Some other title"
