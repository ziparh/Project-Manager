from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from enums.project import ProjectRole
from enums.project_task import ProjectTaskType
from modules.project_members.model import ProjectMember as ProjectMemberModel
from tests.factories.models import ProjectTaskModelFactory, ProjectModelFactory, UserModelFactory


@pytest.mark.integration
class TestUnassignOpenTask:
    """Tests for DELETE /projects/{project_id}/tasks/{task_id}/assign endpoint"""

    async def test_success_own_task_as_owner(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user
    ):
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}/assign"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["id"] == task.id
        assert resp_data["assignee"] is None
        assert resp_data["assigned_at"] is None

        await db_session.refresh(task)
        assert task.assignee_id is None
        assert task.assigned_at is None

    async def test_success_own_task_as_admin(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}/assign"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["assignee"] is None

        await db_session.refresh(task)
        assert task.assignee_id is None

    async def test_success_own_task_as_member(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)],
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}/assign"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["assignee"] is None

        await db_session.refresh(task)
        assert task.assignee_id is None

    async def test_admin_can_unassign_other_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user
    ):
        third_user = UserModelFactory.build()
        db_session.add(third_user)
        await db_session.commit()

        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=third_user.id,
            members=[
                ProjectMemberModel(user_id=test_user.id, role=ProjectRole.ADMIN),
                ProjectMemberModel(user_id=other_user.id, role=ProjectRole.MEMBER),
            ]
        )

        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=other_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=third_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}/assign"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["assignee"] is None

        await db_session.refresh(task)
        assert task.assignee_id is None

    async def test_owner_can_unassign_other_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user,
        other_user
    ):
        member = ProjectMemberModel(
            user_id=other_user.id,
            project_id=test_project.id,
            role=ProjectRole.MEMBER,
        )
        db_session.add(member)
        await db_session.commit()

        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=other_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}/assign"
        )
        resp_data = response.json()

        assert response.status_code == 200
        assert resp_data["assignee"] is None

        await db_session.refresh(task)
        assert task.assignee_id is None

    async def test_member_cannot_unassign_other_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user,
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
            members=[ProjectMemberModel(user_id=test_user.id, role=ProjectRole.MEMBER)]
        )

        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=other_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}/assign"
        )

        assert response.status_code == 403

        await db_session.refresh(task)
        assert task.assignee_id == other_user.id

    async def test_task_not_assigned(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user
    ):
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=None,
            assigned_at=None,
            created_by_id=test_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}/assign"
        )

        assert response.status_code == 400

    async def test_cannot_unassign_default_task(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user
    ):
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.DEFAULT,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}/assign"
        )

        assert response.status_code == 400

    async def test_task_not_found(
        self,
        authenticated_client: AsyncClient,
        test_project
    ):
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/99999/assign"
        )

        assert response.status_code == 404

    async def test_task_from_different_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        test_project
    ):
        other_project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=test_user.id,
        )
        task_from_other_project = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=other_project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task_from_other_project.id}/assign"
        )

        assert response.status_code == 404

    async def test_not_member_of_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user,
        other_user
    ):
        project = await ProjectModelFactory.create(
            session=db_session,
            creator_id=other_user.id,
        )
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=other_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=other_user.id,
        )

        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}/tasks/{task.id}/assign"
        )

        assert response.status_code == 403

        await db_session.refresh(task)
        assert task.assignee_id == other_user.id

    async def test_without_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_project,
        test_user
    ):
        task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.OPEN,
            assignee_id=test_user.id,
            assigned_at=datetime.now(timezone.utc),
            created_by_id=test_user.id,
        )

        response = await client.delete(
            f"/api/v1/projects/{test_project.id}/tasks/{task.id}/assign"
        )

        assert response.status_code == 401

        await db_session.refresh(task)
        assert task.assignee_id == test_user.id
