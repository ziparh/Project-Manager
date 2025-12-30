import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from enums.project_task import ProjectTaskType
from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from enums.project import ProjectRole

from tests.factories.models import ProjectModelFactory, ProjectTaskModelFactory


@pytest.mark.integration
class TestRemoveProjectTask:
    """Tests for DELETE /projects/{project_id}/tasks/{task_id} endpoint"""

    async def test_as_owner(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
    ):
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}"
        )

        assert response.status_code == 204

        db_task = await db_session.get(ProjectTaskModel, test_project_task.id)

        assert not db_task

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
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=project.id,
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}"
        )

        assert response.status_code == 204

        db_task = await db_session.get(ProjectTaskModel, task.id)

        assert not db_task

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
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=project.id,
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}"
        )

        assert response.status_code == 403

        db_task = await db_session.get(ProjectTaskModel, task.id)

        assert db_task

    async def test_task_not_found(
        self, authenticated_client: AsyncClient, test_project
    ):
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/99999"
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

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}"
        )

        assert response.status_code == 403

        db_task = await db_session.get(ProjectTaskModel, task.id)

        assert db_task

    async def test_without_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_project_task,
    ):
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{test_project_task.id}"
        )

        assert response.status_code == 401

        db_task = await db_session.get(ProjectTaskModel, test_project_task.id)

        assert db_task
