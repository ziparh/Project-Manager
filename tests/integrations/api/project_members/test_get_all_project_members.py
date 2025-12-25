import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, UserModelFactory


@pytest.mark.integration
class TestGetAllProjectMembers:
    """Tests for GET /projects{project_id}/members endpoint"""

    async def test_only_in_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        test_project,
    ):
        other_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[ProjectMemberModel(user_id=other_user.id)],
        )

        response = await authenticated_client.get(
            f"api/v1/projects/{other_project.id}/members"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 2
        assert len(resp_data["items"]) == 2

        member_ids = [item["user_id"] for item in resp_data["items"]]

        assert test_user.id in member_ids
        assert other_user.id in member_ids

    async def test_with_filters(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[ProjectMemberModel(user_id=other_user.id, role=ProjectRole.ADMIN)],
        )
        filters = {"role": ProjectRole.ADMIN.value}

        response = await authenticated_client.get(
            f"api/v1/projects/{project.id}/members", params=filters
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 1
        assert len(resp_data["items"]) == 1

        member_data = resp_data["items"][0]

        assert member_data["project_id"] == project.id
        assert member_data["user_id"] == other_user.id
        assert member_data["role"] == ProjectRole.ADMIN.value

    async def test_with_sorting(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[
                ProjectMemberModel(user_id=other_user.id, role=ProjectRole.ADMIN),
                ProjectMemberModel(user_id=user3.id, role=ProjectRole.MEMBER),
            ],
        )
        sorting = {"sort_by": "role", "order": "desc"}

        response = await authenticated_client.get(
            f"api/v1/projects/{project.id}/members", params=sorting
        )
        resp_data = response.json()
        members = resp_data["items"]

        assert response.status_code == 200
        assert resp_data["pagination"]["total"] == 3
        assert len(resp_data["items"]) == 3

        assert members[0]["user_id"] == test_user.id
        assert members[0]["role"] == ProjectRole.OWNER.value
        assert members[1]["user_id"] == other_user.id
        assert members[1]["role"] == ProjectRole.ADMIN.value
        assert members[2]["user_id"] == user3.id
        assert members[2]["role"] == ProjectRole.MEMBER.value

    async def test_with_pagination(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
    ):
        users = [UserModelFactory.build() for _ in range(4)]
        members = [ProjectMemberModel(user_id=user.id) for user in users]

        db_session.add_all(users)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session, creator_id=test_user.id, members=members
        )
        pagination = {"page": 3, "size": 2}

        response = await authenticated_client.get(
            f"api/v1/projects/{project.id}/members", params=pagination
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert len(resp_data["items"]) == 1
        assert resp_data["pagination"]["total"] == 5
        assert resp_data["pagination"]["page"] == 3

    async def test_not_member_of_project(
        self, authenticated_client: AsyncClient, db_session: AsyncSession, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )
        response = await authenticated_client.get(
            f"api/v1/projects/{project.id}/members"
        )

        assert response.status_code == 403

    async def test_without_token(self, client: AsyncClient, test_project):
        response = await client.get(f"api/v1/projects/{test_project.id}/members")

        assert response.status_code == 401
