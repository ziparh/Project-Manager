import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole, ProjectStatus

from tests.factories.models import ProjectModelFactory


@pytest.mark.integration
class TestGetUserProjects:
    """Tests for GET /projects endpoint."""

    async def test_return_only_user_projects(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        for i in range(3):
            await ProjectModelFactory.create(
                session=db_session, creator_id=test_user.id, title=f"Project {i}"
            )
        for i in range(2):
            await ProjectModelFactory.create(
                session=db_session, creator_id=other_user.id, title="Other project"
            )
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Project 3",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )

        response = await authenticated_client.get("api/v1/projects")
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 4
        assert len(resp_data["items"]) == 4

        titles = [item["title"] for item in resp_data["items"]]
        assert "Project 0" in titles
        assert "Project 1" in titles
        assert "Project 2" in titles
        assert "Project 3" in titles
        assert "Other project" not in titles

    async def test_with_filters(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        # Target project
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Target title",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        # Non-matching creator_id
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            title="Target title",
            members=[ProjectMemberModel(user_id=other_user.id, role=ProjectRole.ADMIN)],
        )
        # Non-matching role
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Target title",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        # Non-matching search
        await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            title="Wrong title",
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        filters = {
            "creator_id": other_user.id,
            "role": ProjectRole.ADMIN.value,
            "search": "Target",
        }

        response = await authenticated_client.get("api/v1/projects", params=filters)
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 1
        assert len(resp_data["items"]) == 1

        project_data = resp_data["items"][0]

        assert project_data["creator"]["id"] == other_user.id
        assert project_data["title"] == "Target title"

        user_member = None
        for member in project_data["members"]:
            if member["user_id"] == test_user.id:
                user_member = member

        assert user_member
        assert user_member["role"] == ProjectRole.ADMIN.value

    async def test_with_sorting(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
    ):
        now = datetime.now(timezone.utc)

        p1 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=1),
            status=ProjectStatus.CANCELLED,
        )
        p2 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=2),
            status=ProjectStatus.ACTIVE,
        )
        p3 = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            deadline=now + timedelta(days=3),
            status=ProjectStatus.PLANNING,
        )
        sort1 = {"sort_by": "deadline", "order": "desc"}
        sort2 = {"sort_by": "status", "order": "desc"}

        resp1 = await authenticated_client.get("api/v1/projects", params=sort1)
        resp2 = await authenticated_client.get("api/v1/projects", params=sort2)
        resp1_data = resp1.json()
        resp2_data = resp2.json()
        projects1 = resp1_data["items"]
        projects2 = resp2_data["items"]

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        assert resp1_data["pagination"]["total"] == 3
        assert resp2_data["pagination"]["total"] == 3

        assert projects1[0]["id"] == p3.id
        assert projects1[1]["id"] == p2.id
        assert projects1[2]["id"] == p1.id

        assert projects2[0]["id"] == p1.id
        assert projects2[1]["id"] == p2.id
        assert projects2[2]["id"] == p3.id

    async def test_with_pagination(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user
    ):
        for _ in range(5):
            await ProjectModelFactory.create(
                session=db_session, creator_id=test_user.id
            )
        pagination = {"page": 3, "size": 2}

        response = await authenticated_client.get("api/v1/projects", params=pagination)
        resp_data = response.json()

        assert response.status_code == 200
        assert len(resp_data["items"]) == 1
        assert resp_data["pagination"]["total"] == 5
        assert resp_data["pagination"]["page"] == 3

    async def test_without_token(self, client: AsyncClient):
        response = await client.get("api/v1/projects")

        assert response.status_code == 401
