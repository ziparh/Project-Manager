import pytest
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.model import User as UserModel
from modules.projects.model import Project as ProjectModel
from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from enums.project_task import ProjectTaskType
from enums.task import TaskStatus, TaskPriority
from tests.factories.models import ProjectTaskModelFactory
from utils.datetime import utc_now


@pytest.fixture
async def test_project_task(
    db_session: AsyncSession,
    test_project: ProjectModel,
    test_user: UserModel,
) -> ProjectTaskModel:
    """
    Create a test project task with type 'default'.

    Attributes:
    - id: 1
    - type: DEFAULT
    - project_id: test_project.id (123)
    - assignee_id: test_user.id (123)
    - created_by_id: test_user.id (123)
    - title: Test Task
    - description: Test Description
    - deadline: Now by UTC + 1 day
    - status: TODO
    - priority: MEDIUM
    - assigned_at: Now by UTC
    """
    task = await ProjectTaskModelFactory.create(
        session=db_session,
        id=1,
        type=ProjectTaskType.DEFAULT,
        project_id=test_project.id,
        assignee_id=test_user.id,
        created_by_id=test_user.id,
        title="Test Task",
        description="Test Description",
        deadline=utc_now() + timedelta(days=1),
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        assigned_at=utc_now(),
    )

    return task


@pytest.fixture
async def test_project_open_task(
    db_session: AsyncSession,
    test_project: ProjectModel,
    test_user: UserModel,
) -> ProjectTaskModel:
    """
    Create a test project task with type 'open'.

    Attributes:
    - id: 2
    - type: OPEN
    - project_id: test_project.id (123)
    - assignee_id: None
    - created_by_id: test_user.id (123)
    - title: Open Task
    - description: Open Description
    - deadline: Now by UTC + 2 days
    - status: TODO
    - priority: LOW
    - assigned_at: None
    """
    task = await ProjectTaskModelFactory.create(
        session=db_session,
        id=2,
        type=ProjectTaskType.OPEN,
        project_id=test_project.id,
        assignee_id=None,
        created_by_id=test_user.id,
        title="Open Task",
        description="Open Description",
        deadline=utc_now() + timedelta(days=2),
        status=TaskStatus.TODO,
        priority=TaskPriority.LOW,
        assigned_at=None,
    )

    return task


@pytest.fixture
async def test_multiple_project_tasks(
    db_session: AsyncSession,
    test_project: ProjectModel,
    test_user: UserModel,
    other_user: UserModel,
) -> list[ProjectTaskModel]:
    """
    Create multiple test project tasks with different attributes.

    Returns 5 tasks:
    - task1: HIGH priority, TODO status, assigned to test_user, deadline +2 days
    - task2: MEDIUM priority, IN_PROGRESS status, assigned to other_user, deadline +5 days
    - task3: LOW priority, OPEN type(no assignee), deadline +10 days
    - task4: CRITICAL priority, TODO status, assigned to test_user, OVERDUE (-2 days)
    - task5: MEDIUM priority, DONE status, assigned to other_user, OVERDUE (-1 day)
    """
    now = utc_now()

    tasks = [
        # Task 1
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=test_project.id,
            assignee_id=test_user.id,
            created_by_id=test_user.id,
            title="Task 1 - High Priority",
            description="Description 1",
            deadline=now + timedelta(days=2),
            priority=TaskPriority.HIGH,
            status=TaskStatus.TODO,
            assigned_at=now,
        ),
        # Task 2
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=test_project.id,
            assignee_id=other_user.id,
            created_by_id=test_user.id,
            title="Task 2 - In Progress",
            description="Description 2",
            deadline=now + timedelta(days=5),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.IN_PROGRESS,
            assigned_at=now,
        ),
        # Task 3
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            assignee_id=None,
            created_by_id=test_user.id,
            title="Task 3 - Open",
            description="Description 3",
            deadline=now + timedelta(days=10),
            priority=TaskPriority.LOW,
            status=TaskStatus.TODO,
            assigned_at=None,
        ),
        # Task 4
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=test_project.id,
            assignee_id=other_user.id,
            created_by_id=test_user.id,
            title="Task 4 - Overdue",
            description="Description 4",
            deadline=now - timedelta(days=2),
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.TODO,
            assigned_at=now,
        ),
        # Task 5
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.DEFAULT,
            project_id=test_project.id,
            assignee_id=test_user.id,
            created_by_id=other_user.id,
            title="Task 5 - Done",
            description="Description 5",
            deadline=now - timedelta(days=1),
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.DONE,
            assigned_at=now,
        ),
    ]

    return tasks
