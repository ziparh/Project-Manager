import pytest
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from modules.project_tasks.repository import ProjectTaskRepository
from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from modules.project_tasks.dto import ProjectTaskFilterDto
from common.dto import PaginationDto, SortingDto
from enums.task import TaskStatus, TaskPriority
from enums.project_task import ProjectTaskType
from utils.datetime import utc_now

from tests.factories.models import ProjectTaskModelFactory


@pytest.fixture
async def repo(db_session: AsyncSession) -> ProjectTaskRepository:
    return ProjectTaskRepository(db_session)


@pytest.mark.integration
class TestCreate:
    async def test_with_all_fields_success(
        self, repo, db_session: AsyncSession, test_project, test_user
    ):
        create_data = {
            "type": ProjectTaskType.DEFAULT,
            "title": "Test Task",
            "description": "Test Description",
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.TODO,
            "assignee_id": test_user.id,
            "assigned_at": utc_now(),
            "deadline": utc_now() + timedelta(days=3),
        }

        task = await repo.create(
            project_id=test_project.id,
            created_by_id=test_user.id,
            data=create_data,
        )

        assert isinstance(task.id, int)
        assert task.project_id == test_project.id
        assert task.type == ProjectTaskType.DEFAULT
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.TODO
        assert task.assignee_id == test_user.id
        assert task.assigned_at == create_data["assigned_at"]
        assert task.created_by_id == test_user.id
        assert task.deadline == create_data["deadline"]

        task_in_db = await db_session.get(ProjectTaskModel, task.id)

        assert task_in_db is not None
        assert task_in_db.title == "Test Task"
        assert task_in_db.assignee_id == test_user.id

    async def test_with_minimal_fields_success(
        self, repo, db_session: AsyncSession, test_project, test_user
    ):
        create_data = {
            "type": ProjectTaskType.OPEN,
            "title": "Minimal Task",
        }

        task = await repo.create(
            project_id=test_project.id,
            created_by_id=test_user.id,
            data=create_data,
        )

        assert isinstance(task.id, int)
        assert task.project_id == test_project.id
        assert task.title == "Minimal Task"
        assert task.type == ProjectTaskType.OPEN
        assert task.assignee_id is None
        assert task.assigned_at is None

        task_in_db = await db_session.get(ProjectTaskModel, task.id)

        assert task_in_db is not None
        assert task_in_db.title == "Minimal Task"

    async def test_create_open_task_success(
        self, repo, db_session: AsyncSession, test_project, test_user
    ):
        create_data = {
            "type": ProjectTaskType.OPEN,
            "title": "Open Task",
            "description": "Available for anyone",
            "priority": TaskPriority.MEDIUM,
            "status": TaskStatus.TODO,
        }

        task = await repo.create(
            project_id=test_project.id,
            created_by_id=test_user.id,
            data=create_data,
        )

        assert task.type == ProjectTaskType.OPEN
        assert task.assignee_id is None
        assert task.assigned_at is None


@pytest.mark.integration
class TestGetAll:
    async def test_success(self, repo, test_project, test_multiple_project_tasks):
        filters = ProjectTaskFilterDto()
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert len(items) == 5

    async def test_with_type_filter(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(type=ProjectTaskType.OPEN)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].type == ProjectTaskType.OPEN
        assert items[0].title == "Task 3 - Open"

    async def test_with_assignee_filter(
        self, repo, test_project, test_user, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(assignee_id=test_user.id)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 2  # task1 and task5
        for item in items:
            assert item.assignee_id == test_user.id

    async def test_with_created_by_filter(
        self, repo, test_project, test_user, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(created_by_id=test_user.id)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 4  # Only 1 task created by other_user
        for item in items:
            assert item.created_by_id == test_user.id

    async def test_with_status_filter(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(status=TaskStatus.TODO)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3  # task1, task3, task4
        for item in items:
            assert item.status == TaskStatus.TODO

    async def test_with_priority_filter(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(priority=TaskPriority.HIGH)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1  # task1
        assert items[0].priority == TaskPriority.HIGH

    @pytest.mark.parametrize(
        "overdue, expected_count, expected_titles",
        [
            (True, 1, ["Task 4 - Overdue"]),  # Only task4 (overdue and not done)
            (
                False,
                4,
                [
                    "Task 1 - High Priority",
                    "Task 2 - In Progress",
                    "Task 3 - Open",
                    "Task 5 - Done",
                ],
            ),
        ],
    )
    async def test_with_overdue_filter(
        self,
        repo,
        test_project,
        test_multiple_project_tasks,
        overdue: bool,
        expected_count: int,
        expected_titles: list[str],
    ):
        filters = ProjectTaskFilterDto(overdue=overdue)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == expected_count
        titles = [item.title for item in items]
        for expected_title in expected_titles:
            assert expected_title in titles

    async def test_with_search_filter_by_title(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(search="High Priority")
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert "High Priority" in items[0].title

    async def test_with_search_filter_by_description(
        self, repo, db_session: AsyncSession, test_project, test_user
    ):
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            description="Backend for JavaScript website on Python",
            created_by_id=test_user.id,
        )
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            description="JavaScript website",
            created_by_id=test_user.id,
        )
        await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            description="Fix coffee machine in the office",
            created_by_id=test_user.id,
        )

        filters = ProjectTaskFilterDto(search="javascript")
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 2
        for item in items:
            assert "JavaScript" in item.description

    async def test_with_search_filter_by_username(
        self, repo, test_project, other_user, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto(search=other_user.username)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        # Should find tasks assigned to or created by other_user
        assert total == 3

    async def test_with_multiple_filters(
        self, repo, db_session: AsyncSession, test_project, test_user, other_user
    ):
        # Target task
        target_task = await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.DEFAULT,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id=test_user.id,
            assigned_at=utc_now(),
            created_by_id=test_user.id,
        )
        # Non-matching status
        await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.DEFAULT,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            assignee_id=test_user.id,
            assigned_at=utc_now(),
            created_by_id=test_user.id,
        )
        # Non-matching assignee
        await ProjectTaskModelFactory.create(
            session=db_session,
            project_id=test_project.id,
            type=ProjectTaskType.DEFAULT,
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id=other_user.id,
            assigned_at=utc_now(),
            created_by_id=test_user.id,
        )

        filters = ProjectTaskFilterDto(
            type=ProjectTaskType.DEFAULT,
            status=TaskStatus.IN_PROGRESS,
            assignee_id=test_user.id,
            priority=TaskPriority.HIGH,
        )
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].id == target_task.id

    async def test_with_sorting_by_deadline_asc(
        self, repo, db_session: AsyncSession, test_project, test_user
    ):
        now = utc_now()
        t1 = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            title="Task 1",
            deadline=now + timedelta(days=1),
            created_by_id=test_user.id,
        )
        t2 = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            title="Task 2",
            deadline=now + timedelta(days=2),
            created_by_id=test_user.id,
        )
        t3 = await ProjectTaskModelFactory.create(
            session=db_session,
            type=ProjectTaskType.OPEN,
            project_id=test_project.id,
            title="Task 3",
            deadline=now + timedelta(days=3),
            created_by_id=test_user.id,
        )

        filters = ProjectTaskFilterDto()
        sorting = SortingDto(sort_by="deadline", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3
        assert items[0].id == t1.id
        assert items[1].id == t2.id
        assert items[2].id == t3.id

    async def test_with_sorting_by_priority_desc(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto()
        sorting = SortingDto(sort_by="priority", order="desc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        # First should be CRITICAL (task4)
        assert items[0].priority == TaskPriority.CRITICAL
        # Second should be HIGH (task1)
        assert items[1].priority == TaskPriority.HIGH

    async def test_with_pagination(
        self, repo, test_project, test_multiple_project_tasks
    ):
        filters = ProjectTaskFilterDto()
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=2, offset=2)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert len(items) == 2

    async def test_not_found(self, repo, test_project):
        filters = ProjectTaskFilterDto(status=TaskStatus.CANCELLED)
        sorting = SortingDto(sort_by="created_at", order="asc")
        pagination = PaginationDto(size=10, offset=0)

        items, total = await repo.get_all(
            project_id=test_project.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 0
        assert len(items) == 0


@pytest.mark.integration
class TestGetById:
    async def test_found(self, repo, test_project_task):
        task = await repo.get_by_id(test_project_task.id)

        assert task is not None
        assert task.id == test_project_task.id
        assert task.title == test_project_task.title

    async def test_not_found(self, repo):
        task = await repo.get_by_id(99999)

        assert task is None


@pytest.mark.integration
class TestUpdateByTask:
    async def test_all_fields_success(
        self, repo, db_session: AsyncSession, test_project_task, other_user
    ):
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
            "priority": TaskPriority.CRITICAL,
            "status": TaskStatus.IN_PROGRESS,
            "assignee_id": other_user.id,
            "deadline": utc_now() + timedelta(days=10),
        }

        updated_task = await repo.update_by_task(
            task=test_project_task,
            data=update_data,
        )

        assert updated_task.id == test_project_task.id
        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Updated Description"
        assert updated_task.priority == TaskPriority.CRITICAL
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.assignee_id == other_user.id
        assert updated_task.deadline == update_data["deadline"]

        await db_session.refresh(test_project_task)

        assert test_project_task.title == "Updated Title"
        assert test_project_task.description == "Updated Description"
        assert test_project_task.priority == TaskPriority.CRITICAL
        assert test_project_task.status == TaskStatus.IN_PROGRESS
        assert test_project_task.assignee_id == other_user.id
        assert test_project_task.deadline == update_data["deadline"]

    async def test_minimal_fields_success(
        self, repo, db_session: AsyncSession, test_project_task
    ):
        original_description = test_project_task.description
        original_priority = test_project_task.priority

        update_data = {"title": "New Title Only"}

        updated_task = await repo.update_by_task(
            task=test_project_task,
            data=update_data,
        )

        assert updated_task.id == test_project_task.id
        assert updated_task.title == "New Title Only"
        assert updated_task.description == original_description
        assert updated_task.priority == original_priority

        await db_session.refresh(test_project_task)

        assert test_project_task.title == "New Title Only"
        assert test_project_task.description == original_description
        assert test_project_task.priority == original_priority


@pytest.mark.integration
class TestDeleteByTask:
    async def test_success(self, repo, db_session: AsyncSession, test_project_task):
        task_id = test_project_task.id

        await repo.delete_by_task(test_project_task)

        deleted_task = await db_session.get(ProjectTaskModel, task_id)

        assert deleted_task is None
