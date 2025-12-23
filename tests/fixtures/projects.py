import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.model import User as UserModel
from modules.projects.model import Project as ProjectModel
from enums.project import ProjectStatus

from tests.factories.models import ProjectModelFactory


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: UserModel) -> ProjectModel:
    """
    Create a test project owned by test_user with fixed and known attributes.

    Attributes:
    - id: 123
    - Creator_id: test_user.id (123)
    - Title: Test Title
    - Description: Test Description
    - Deadline: Now by UTC + 1 day
    - Status: ProjectStatus.ACTIVE (active)
    """
    project = await ProjectModelFactory.create(
        session=db_session,
        id=123,
        creator_id=test_user.id,
        title="Test Title",
        description="Test Description",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        status=ProjectStatus.ACTIVE,
    )

    return project


@pytest.fixture
async def test_multiple_projects(
    db_session: AsyncSession, test_user: UserModel
) -> list[ProjectModel]:
    """Create multiple projects owned by test_user."""
    projects = [
        await ProjectModelFactory.create(session=db_session, creator_id=test_user.id)
        for _ in range(3)
    ]

    return projects


@pytest.fixture
async def other_multiple_projects(
    db_session: AsyncSession, other_user: UserModel
) -> list[ProjectModel]:
    """Create multiple projects owned by another user."""
    projects = [
        await ProjectModelFactory.create(session=db_session, creator_id=other_user.id)
        for _ in range(3)
    ]

    return projects
