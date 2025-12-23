import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole, ProjectStatus

from tests.factories.models import ProjectModelFactory


@pytest.mark.integration
class TestPatchProject:
    """Tests for PATCH /projects/{project_id} endpoint"""

    async def test_as_owner(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_project
    ):
        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"api/v1/projects/{test_project.id}", json=update_data
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["title"] == update_data["title"]

    async def test_as_admin(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Old title",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}", json=update_data
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["title"] == update_data["title"]

    async def test_as_member(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Old title",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        update_data = {"title": "New title"}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}", json=update_data
        )

        assert response.status_code == 403

        await db_session.refresh(project)

        assert project.title != update_data["title"]

    async def test_with_all_data(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_project
    ):
        deadline = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        update_data = {
            "title": "New title",
            "description": "New description",
            "deadline": deadline,
            "status": ProjectStatus.COMPLETED.value,
        }

        response = await authenticated_client.patch(
            f"api/v1/projects/{test_project.id}", json=update_data
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project.id
        assert resp_data["title"] == update_data["title"]
        assert resp_data["description"] == update_data["description"]
        assert resp_data["deadline"].replace("Z", "+00:00") == update_data["deadline"]
        assert resp_data["status"] == update_data["status"]

        await db_session.refresh(test_project)

        assert test_project.title == update_data["title"]
        assert test_project.description == update_data["description"]
        assert test_project.deadline.isoformat() == update_data["deadline"]
        assert test_project.status == ProjectStatus.COMPLETED

    @pytest.mark.parametrize(
        "update_data, changed_field",
        [
            ({"title": "New title"}, "title"),
            ({"description": "New description"}, "description"),
            ({"status": ProjectStatus.COMPLETED.value}, "status"),
        ],
    )
    async def test_with_partial_data(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        update_data,
        changed_field,
    ):
        response = await authenticated_client.patch(
            f"api/v1/projects/{test_project.id}", json=update_data
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == test_project.id
        assert resp_data[changed_field] == update_data[changed_field]

        await db_session.refresh(test_project)

        db_field = getattr(test_project, changed_field)

        if hasattr(db_field, "value"):  # For enums
            assert db_field.value == update_data[changed_field]
        else:
            assert db_field == update_data[changed_field]

    async def test_not_member(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}", json={"title": "Test"}
        )

        assert response.status_code == 403

        await db_session.refresh(project)

        assert project.title != "Test"

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_project
    ):
        response = await client.patch(
            f"api/v1/projects/{test_project.id}", json={"title": "Test"}
        )

        assert response.status_code == 401

        await db_session.refresh(test_project)

        assert test_project.title != "Test"
