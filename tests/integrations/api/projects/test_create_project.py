import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.projects.model import Project as ProjectModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectStatus, ProjectRole


@pytest.mark.integration
class TestCreateProject:
    """Tests for POST /projects endpoint"""

    async def test_with_all_data(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        deadline = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        project_data = {
            "title": "Test Project",
            "description": "Some description",
            "deadline": deadline,
            "status": ProjectStatus.ACTIVE.value,
        }

        response = await authenticated_client.post("api/v1/projects", json=project_data)
        resp_data = response.json()

        assert response.status_code == 201

        db_project = await db_session.get(ProjectModel, resp_data["id"])

        assert db_project is not None
        assert resp_data["title"] == db_project.title
        assert resp_data["description"] == db_project.description
        assert resp_data["deadline"] == db_project.deadline.isoformat().replace(
            "+00:00", "Z"
        )
        assert resp_data["status"] == db_project.status.value

    async def test_with_minimal_data(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        project_data = {"title": "Test Project"}

        response = await authenticated_client.post("api/v1/projects", json=project_data)
        resp_data = response.json()

        db_project = await db_session.get(ProjectModel, resp_data["id"])

        assert response.status_code == 201

        assert db_project is not None
        assert resp_data["title"] == db_project.title
        assert db_project.description is None
        assert db_project.deadline is None
        assert db_project.status == ProjectStatus.PLANNING  # Status by default

    async def test_creator_is_owner(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        project_data = {"title": "Test Project"}

        response = await authenticated_client.post("api/v1/projects", json=project_data)

        assert response.status_code == 201

        project_id = response.json()["id"]
        stmt = select(ProjectMemberModel).where(
            ProjectMemberModel.project_id == project_id,
            ProjectMemberModel.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        member = result.scalar_one_or_none()

        assert member is not None
        assert member.role == ProjectRole.OWNER

    @pytest.mark.parametrize(
        "invalid_data, expected_field",
        [
            ({"title": ""}, "title"),
            ({"title": "f" * 201}, "title"),  # Title max length is 200
            (
                {"title": "Test", "description": "f" * 1001},
                "description",
            ),  # Description max length is 1000
        ],
    )
    async def test_validation_errors(
        self, authenticated_client: AsyncClient, invalid_data, expected_field
    ):
        response = await authenticated_client.post("api/v1/projects", json=invalid_data)

        assert response.status_code == 422

        errors = response.json()["detail"]
        assert any(expected_field in str(error["loc"]) for error in errors)

    async def test_without_token(self, client: AsyncClient):
        response = await client.post("api/v1/projects")

        assert response.status_code == 401
