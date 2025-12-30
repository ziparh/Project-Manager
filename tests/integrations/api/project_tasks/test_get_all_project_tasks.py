import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from enums.project_task import ProjectTaskType
from enums.task import TaskStatus, TaskPriority

from tests.factories.models import ProjectModelFactory, ProjectTaskModelFactory


@pytest.mark.integration
class TestGetAllProjectTasks:
    """Tests for GET /projects/{project_id}/tasks endpoint"""

    async def test_return_only_project_tasks(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project,
        test_multiple_project_tasks,
    ):
        other_project = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id
        )
        for _ in range(2):
            await ProjectTaskModelFactory.create(
                session=db_session,
                type=ProjectTaskType.OPEN,
                project_id=other_project.id,
                created_by_id=test_user.id,
                title="Other task",
            )

        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 5
        assert len(resp_data["items"]) == 5

        task_ids = [item["id"] for item in resp_data["items"]]
        for task in test_multiple_project_tasks:
            assert task.id in task_ids

    async def test_with_filters(
        self,
        authenticated_client: AsyncClient,
        test_project,
        test_user,
        other_user,
        test_multiple_project_tasks,
    ):
        filters = {
            "status": TaskStatus.TODO.value,
            "assignee_id": test_user.id,
        }

        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks", params=filters
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 1  # Only task1
        assert len(resp_data["items"]) == 1

        task_data = resp_data["items"][0]
        assert task_data["id"] == test_multiple_project_tasks[0].id
        assert task_data["status"] == TaskStatus.TODO.value
        assert task_data["assignee"]["id"] == test_user.id
        assert task_data["priority"] == TaskPriority.HIGH.value

    async def test_with_sorting(
        self,
        authenticated_client: AsyncClient,
        test_project,
        test_multiple_project_tasks,
    ):
        sort1 = {"sort_by": "deadline", "order": "asc"}
        sort2 = {"sort_by": "priority", "order": "desc"}

        resp1 = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks", params=sort1
        )
        resp2 = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks", params=sort2
        )
        resp1_data = resp1.json()
        resp2_data = resp2.json()
        tasks1 = resp1_data["items"]
        tasks2 = resp2_data["items"]

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        assert resp1_data["pagination"]["total"] == 5
        assert resp2_data["pagination"]["total"] == 5

        # Sort by deadline asc
        assert tasks1[0]["id"] == test_multiple_project_tasks[3].id  # task4: -2 days
        assert tasks1[1]["id"] == test_multiple_project_tasks[4].id  # task5: -1 day
        assert tasks1[2]["id"] == test_multiple_project_tasks[0].id  # task1: +2 days
        assert tasks1[3]["id"] == test_multiple_project_tasks[1].id  # task2: +5 days
        assert tasks1[4]["id"] == test_multiple_project_tasks[2].id  # task3: +10 days

        # Sort by priority desc
        assert tasks2[0]["id"] == test_multiple_project_tasks[3].id  # task4: CRITICAL
        assert tasks2[1]["id"] == test_multiple_project_tasks[0].id  # task1: HIGH
        assert tasks2[4]["id"] == test_multiple_project_tasks[2].id  # task3: LOW

    async def test_with_pagination(
        self,
        authenticated_client: AsyncClient,
        test_project,
        test_multiple_project_tasks,
    ):
        pagination = {"page": 2, "size": 2}

        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks", params=pagination
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert len(resp_data["items"]) == 2
        assert resp_data["pagination"]["total"] == 5
        assert resp_data["pagination"]["page"] == 2
        assert resp_data["pagination"]["size"] == 2

    async def test_not_member_of_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )

        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}/tasks"
        )

        assert response.status_code == 403

    async def test_without_token(self, client: AsyncClient, test_project):
        response = await client.get(f"/api/v1/projects/{test_project.id}/tasks")

        assert response.status_code == 401
