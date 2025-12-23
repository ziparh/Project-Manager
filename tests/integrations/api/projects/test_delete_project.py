import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.projects.model import Project as ProjectModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory


@pytest.mark.integration
class TestCreateProject:
    """Tests for DELETE /projects/{project_id} endpoint"""

    async def test_as_owner(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_project
    ):
        response = await authenticated_client.delete(
            f"api/v1/projects/{test_project.id}"
        )

        assert response.status_code == 204

        db_project = await db_session.get(ProjectModel, test_project.id)

        assert not db_project

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

        response = await authenticated_client.delete(f"api/v1/projects/{project.id}")

        assert response.status_code == 403

        db_project = await db_session.get(ProjectModel, project.id)

        assert db_project

    async def test_not_member(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
        )

        response = await authenticated_client.delete(f"api/v1/projects/{project.id}")

        assert response.status_code == 403

        db_project = await db_session.get(ProjectModel, project.id)

        assert db_project

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_project
    ):
        response = await client.delete(f"api/v1/projects/{test_project.id}")

        assert response.status_code == 401

        db_project = await db_session.get(ProjectModel, test_project.id)

        assert db_project
