import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members import model
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, UserModelFactory


@pytest.mark.integration
class TestUpdateProjectMember:
    """Tests for PATCH /projects{project_id}/members/{user_id} endpoint"""

    @pytest.mark.parametrize(
        "role, updated_role",
        [
            (ProjectRole.MEMBER, ProjectRole.ADMIN),
            (ProjectRole.ADMIN, ProjectRole.MEMBER),
        ],
    )
    async def test_owner_can_update(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        role,
        updated_role,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[model.ProjectMember(user_id=other_user.id, role=role)],
        )
        update_data = {"role": updated_role.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}/members/{other_user.id}", json=update_data
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["user_id"] == other_user.id
        assert resp_data["role"] == updated_role.value

        db_membership = await db_session.get(model.ProjectMember, resp_data["id"])

        assert db_membership.project_id == project.id
        assert db_membership.user_id == other_user.id
        assert db_membership.role == updated_role

    async def test_admin_can_update_member(
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
            members=[
                model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN),
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.MEMBER),
            ],
        )

        update_data = {"role": ProjectRole.MEMBER.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}/members/{other_user.id}", json=update_data
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "role, updated_role",
        [
            (ProjectRole.OWNER, ProjectRole.ADMIN),
            (ProjectRole.ADMIN, ProjectRole.MEMBER),
            (ProjectRole.MEMBER, ProjectRole.ADMIN),
        ],
    )
    async def test_admin_cannot_update(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        role,
        updated_role,
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=user3.id,
            members=[
                model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN),
                model.ProjectMember(user_id=other_user.id, role=role),
            ],
        )

        update_data = {"role": updated_role.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}/members/{other_user.id}", json=update_data
        )

        assert response.status_code == 403

    async def test_member_cannot_update(
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
            members=[
                model.ProjectMember(user_id=test_user.id, role=ProjectRole.MEMBER),
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.MEMBER),
            ],
        )

        update_data = {"role": ProjectRole.MEMBER.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}/members/{other_user.id}", json=update_data
        )

        assert response.status_code == 403

    async def test_member_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        update_data = {"role": ProjectRole.MEMBER.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{test_project.id}/members/9999", json=update_data
        )

        assert response.status_code == 404

    async def test_not_member_of_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        other_user,
    ):
        user3 = UserModelFactory.build()
        db_session.add(user3)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[model.ProjectMember(user_id=user3.id, role=ProjectRole.MEMBER)],
        )
        update_data = {"role": ProjectRole.ADMIN.value}

        response = await authenticated_client.patch(
            f"api/v1/projects/{project.id}/members/{user3.id}", json=update_data
        )

        assert response.status_code == 403

    async def test_without_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.MEMBER)
            ],
        )
        update_data = {"role": ProjectRole.ADMIN.value}

        response = await client.patch(
            f"api/v1/projects/{project.id}/members/{other_user.id}", json=update_data
        )

        assert response.status_code == 401
