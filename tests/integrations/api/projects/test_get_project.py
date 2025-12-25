import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory


@pytest.mark.integration
class TestCreateProject:
    """Tests for GET /projects/{project_id} endpoint"""

    async def test_as_owner(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_project
    ):
        response = await authenticated_client.get(f"/api/v1/projects/{test_project.id}")
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project.id

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

        response = await authenticated_client.get(f"/api/v1/projects/{project.id}")
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == project.id

    async def test_not_member(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )

        response = await authenticated_client.get(f"/api/v1/projects/{project.id}")

        assert response.status_code == 403

    async def test_without_token(self, client: AsyncClient, test_project):
        response = await client.get(f"/api/v1/projects/{test_project.id}")

        assert response.status_code == 401
