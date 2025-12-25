import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_members import model
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, UserModelFactory


@pytest.mark.integration
class TestRemoveProjectMember:
    """Tests for DELETE /projects{project_id}/members/{user_id} endpoint"""

    @pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER])
    async def test_owner_can_remove(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
        role,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[model.ProjectMember(user_id=other_user.id, role=role)],
        )

        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{other_user.id}"
        )

        assert response.status_code == 204

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == other_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert not db_membership

    async def test_admin_can_remove(
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

        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{other_user.id}"
        )

        assert response.status_code == 204

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == other_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert not db_membership

    @pytest.mark.parametrize("role", [ProjectRole.OWNER, ProjectRole.ADMIN])
    async def test_admin_cannot_remove(
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
                model.ProjectMember(user_id=test_user.id, role=ProjectRole.ADMIN),
                model.ProjectMember(user_id=other_user.id, role=role),
            ],
        )

        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{other_user.id}"
        )

        assert response.status_code == 403

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == other_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert db_membership

    async def test_member_cannot_remove(
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

        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{other_user.id}"
        )

        assert response.status_code == 403

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == other_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert db_membership

    async def test_owner_cannot_remove_themselves(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user,
    ):
        response = await authenticated_client.delete(
            f"api/v1/projects/{test_project.id}/members/{test_user.id}"
        )

        assert response.status_code == 400

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == test_project.id,
            model.ProjectMember.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert db_membership

    @pytest.mark.parametrize("role", [ProjectRole.ADMIN, ProjectRole.MEMBER])
    async def test_other_roles_can_remove_themselves(
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
            members=[model.ProjectMember(user_id=test_user.id, role=role)],
        )
        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{test_user.id}"
        )

        assert response.status_code == 204

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert not db_membership

    async def test_member_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        response = await authenticated_client.delete(
            f"api/v1/projects/{test_project.id}/members/9999"
        )

        assert response.status_code == 404

    async def test_not_member_of_project(
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
            creator_id=other_user.id,
            members=[model.ProjectMember(user_id=user3.id, role=ProjectRole.MEMBER)],
        )

        response = await authenticated_client.delete(
            f"api/v1/projects/{project.id}/members/{user3.id}"
        )

        assert response.status_code == 403

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == user3.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert db_membership

    async def test_without_token(
        self, client: AsyncClient, db_session: AsyncSession, test_user, other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
            members=[
                model.ProjectMember(user_id=other_user.id, role=ProjectRole.MEMBER)
            ],
        )

        response = await client.delete(
            f"api/v1/projects/{project.id}/members/{other_user.id}"
        )

        assert response.status_code == 401

        stmt = select(model.ProjectMember).where(
            model.ProjectMember.project_id == project.id,
            model.ProjectMember.user_id == other_user.id,
        )
        result = await db_session.execute(stmt)
        db_membership = result.scalar_one_or_none()

        assert db_membership
