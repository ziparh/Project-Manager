import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members import model
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, UserModelFactory


@pytest.mark.integration
class TestAddProjectMember:
    """Tests for POST /projects/{project_id}/members endpoint"""

    @pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER])
    async def test_owner_can_add(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        other_user,
        role,
    ):
        data_to_add = {
            "user_id": other_user.id,
            "role": role.value,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{test_project.id}/members", json=data_to_add
        )
        resp_data = response.json()

        assert response.status_code == 201
        assert resp_data["project_id"] == test_project.id
        assert resp_data["user_id"] == other_user.id
        assert resp_data["role"] == role.value

        db_membership = await db_session.get(model.ProjectMember, resp_data["id"])

        assert db_membership.project_id == test_project.id
        assert db_membership.user_id == other_user.id
        assert db_membership.role == role

    async def test_owner_cannot_add(
        self, authenticated_client: AsyncClient, test_project, other_user
    ):
        data_to_add = {
            "user_id": other_user.id,
            "role": ProjectRole.OWNER.value,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{test_project.id}/members", json=data_to_add
        )

        assert response.status_code == 400

    async def test_admin_can_add(
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
            creator_id=user3.id,
            members=[model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )

        data_to_add = {
            "user_id": other_user.id,
            "role": ProjectRole.MEMBER.value,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{project.id}/members", json=data_to_add
        )

        resp_data = response.json()

        assert response.status_code == 201
        assert resp_data["project_id"] == project.id
        assert resp_data["user_id"] == other_user.id
        assert resp_data["role"] == ProjectRole.MEMBER.value

        db_membership = await db_session.get(model.ProjectMember, resp_data["id"])

        assert db_membership.project_id == project.id
        assert db_membership.user_id == other_user.id
        assert db_membership.role == ProjectRole.MEMBER

    async def test_admin_cannot_add(
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
            creator_id=user3.id,
            members=[model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )

        data_to_add = {
            "user_id": other_user.id,
            "role": ProjectRole.ADMIN.value,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{project.id}/members", json=data_to_add
        )

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "role", [ProjectRole.ADMIN.value, ProjectRole.MEMBER.value]
    )
    async def test_member_cannot_add(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        role,
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=user3.id,
            members=[
                model.ProjectMember(user_id=test_user.id, role=ProjectRole.MEMBER)
            ],
        )

        data_to_add = {
            "user_id": other_user.id,
            "role": role,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{project.id}/members", json=data_to_add
        )

        assert response.status_code == 403

    async def test_user_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        data_to_add = {
            "user_id": 9999,
            "role": ProjectRole.MEMBER.value,
        }
        response = await authenticated_client.post(
            f"api/v1/projects/{test_project.id}/members", json=data_to_add
        )

        assert response.status_code == 404

    async def test_not_member_of_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        other_user,
        test_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session, creator_id=other_user.id
        )
        data_to_add = {
            "user_id": test_user.id,
            "role": ProjectRole.MEMBER.value,
        }

        response = await authenticated_client.post(
            f"api/v1/projects/{project.id}/members", json=data_to_add
        )

        assert response.status_code == 403

    async def test_with_out_token(self, client: AsyncClient, test_project, test_user):
        data_to_add = {
            "user_id": test_user.id,
            "role": ProjectRole.MEMBER.value,
        }
        response = await client.post(
            f"api/v1/projects/{test_project.id}/members", json=data_to_add
        )

        assert response.status_code == 401
