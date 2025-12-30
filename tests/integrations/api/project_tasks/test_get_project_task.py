import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole
from enums.project_task import ProjectTaskType

from tests.factories.models import ProjectModelFactory, ProjectTaskModelFactory


@pytest.mark.integration
class TestGetProjectTask:
    """Tests for GET /projects/{project_id}/tasks/{task_id} endpoint"""

    async def test_as_owner(
        self, authenticated_client: AsyncClient, test_project, test_project_task
    ):
        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project_task.id
        assert resp_data["project"]["id"] == test_project.id
        assert resp_data["title"] == test_project_task.title

    @pytest.mark.parametrize(
        "role",
        [
            ProjectRole.ADMIN,
            ProjectRole.MEMBER,
        ],
    )
    async def test_as_other_roles(
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
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=project.id,
            created_by_id=other_user.id,
        )

        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}/tasks/{task.id}"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data["project"]["id"] == project.id

    async def test_task_from_different_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project,
    ):
        other_project = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id
        )
        task_from_other_project = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=other_project.id,
            created_by_id=test_user.id,
        )

        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks/{task_from_other_project.id}"
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

        response = await authenticated_client.get(
            f"/api/v1/projects/{project.id}/tasks/{task.id}"
        )

        assert response.status_code == 403

    async def test_task_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        response = await authenticated_client.get(
            f"/api/v1/projects/{test_project.id}/tasks/99999"
        )

        assert response.status_code == 404

    async def test_without_token(
        self, client: AsyncClient, test_project, test_project_task
    ):
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}"
        )

        assert response.status_code == 401
