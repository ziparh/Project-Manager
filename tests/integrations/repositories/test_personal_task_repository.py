import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from modules.personal_tasks import repository, model, dto as tasks_dto
from common import dto as common_dto
from enums.task import TaskStatus, TaskPriority

from tests.factories.models import PersonalTaskModelFactory


@pytest.fixture
def repo(db_session: AsyncSession) -> repository.PersonalTaskRepository:
    return repository.PersonalTaskRepository(db_session)


@pytest.mark.integration
class TestGetList:
    async def test_returns_only_user_tasks(
        self, repo, test_user, other_user, db_session: AsyncSession
    ):
        task1 = PersonalTaskModelFactory.build(user_id=test_user.id, title="Task 1")
        task2 = PersonalTaskModelFactory.build(user_id=test_user.id, title="Task 2")
        task3 = PersonalTaskModelFactory.build(user_id=other_user.id, title="Task 3")

        db_session.add_all([task1, task2, task3])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto()
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        task_ids = [task1.id, task2.id]
        task_titles = [task1.title, task2.title]

        assert total == 2
        assert len(items) == 2
        assert items[0].id in task_ids
        assert items[0].title in task_titles
        assert items[1].id in task_ids
        assert items[1].title in task_titles

    async def test_with_status_filter(self, repo, db_session: AsyncSession, test_user):
        task_todo = PersonalTaskModelFactory.build(
            user_id=test_user.id, status=TaskStatus.TODO
        )
        task_done = PersonalTaskModelFactory.build(
            user_id=test_user.id, status=TaskStatus.DONE
        )

        db_session.add_all([task_todo, task_done])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto(status=TaskStatus.TODO)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].status == TaskStatus.TODO

    async def test_with_priority_filter(
        self, repo, db_session: AsyncSession, test_user
    ):
        task_low = PersonalTaskModelFactory.build(
            user_id=test_user.id, priority=TaskPriority.LOW
        )
        task_high = PersonalTaskModelFactory.build(
            user_id=test_user.id, priority=TaskPriority.HIGH
        )

        db_session.add_all([task_low, task_high])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto(priority=TaskPriority.LOW)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].priority == TaskPriority.LOW

    async def test_with_overdue_filter_true(
        self, repo, db_session: AsyncSession, test_user
    ):

        now = datetime.now(timezone.utc)

        overdue_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=now - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        future_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=now + timedelta(days=1),
            status=TaskStatus.TODO,
        )
        completed_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=now - timedelta(days=1),
            status=TaskStatus.DONE,
        )

        db_session.add_all([overdue_task, future_task, completed_task])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto(overdue=True)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 1
        assert items[0].id == overdue_task.id

    async def test_with_overdue_filter_false(
        self, repo, db_session: AsyncSession, test_user
    ):

        now = datetime.now(timezone.utc)

        overdue_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=now - timedelta(days=1),
            status=TaskStatus.IN_PROGRESS,
        )
        future_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=now + timedelta(days=1),
            status=TaskStatus.TODO,
        )
        no_deadline_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            deadline=None,
            status=TaskStatus.DONE,
        )

        db_session.add_all([overdue_task, future_task, no_deadline_task])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto(overdue=False)
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
        task_ids = [future_task.id, no_deadline_task.id]

        assert total == 2
        assert items[0].id in task_ids
        assert items[1].id in task_ids

    async def test_with_search_filter(self, repo, db_session: AsyncSession, test_user):
        meeting_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            title="Important meeting",
            description="Business",
        )
        dinner_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            title="Family dinner",
            description="Fish",
        )
        products_task = PersonalTaskModelFactory.build(
            user_id=test_user.id,
            title="Buy products",
            description="Fish for dinner",
        )

        db_session.add_all([meeting_task, dinner_task, products_task])
        await db_session.commit()

        filters1 = tasks_dto.PersonalTaskFilterDto(search="important")
        filters2 = tasks_dto.PersonalTaskFilterDto(search="dinner")
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items1, total1 = await repo.get_list(
            user_id=test_user.id,
            filters=filters1,
            sorting=sorting,
            pagination=pagination,
        )

        items2, total2 = await repo.get_list(
            user_id=test_user.id,
            filters=filters2,
            sorting=sorting,
            pagination=pagination,
        )

        assert total1 == 1
        assert items1[0].id == meeting_task.id

        task_with_dinner_ids = [dinner_task.id, products_task.id]
        assert total2 == 2
        assert items2[0].id in task_with_dinner_ids
        assert items2[1].id in task_with_dinner_ids

    async def test_with_sorting_asc(self, repo, db_session: AsyncSession, test_user):
        now = datetime.now(timezone.utc)
        task_1 = PersonalTaskModelFactory.build(
            user_id=test_user.id, deadline=now + timedelta(days=3)
        )
        task_2 = PersonalTaskModelFactory.build(
            user_id=test_user.id, deadline=now + timedelta(days=1)
        )
        task_3 = PersonalTaskModelFactory.build(
            user_id=test_user.id, deadline=now + timedelta(days=2)
        )

        db_session.add_all([task_1, task_2, task_3])
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto()
        sorting = common_dto.SortingDto(sort_by="deadline", order="asc")
        pagination = common_dto.PaginationDto(size=10, offset=0)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 3
        assert items[0].id == task_2.id
        assert items[1].id == task_3.id
        assert items[2].id == task_1.id

    async def test_with_pagination(self, repo, db_session: AsyncSession, test_user):
        tasks = [PersonalTaskModelFactory.build(user_id=test_user.id) for _ in range(5)]

        db_session.add_all(tasks)
        await db_session.commit()

        filters = tasks_dto.PersonalTaskFilterDto()
        sorting = common_dto.SortingDto(sort_by="created_at", order="asc")
        pagination = common_dto.PaginationDto(size=2, offset=2)

        items, total = await repo.get_list(
            user_id=test_user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert total == 5
        assert len(items) == 2


@pytest.mark.integration
class TestGetByIdAndUser:
    async def test_success(self, repo, db_session: AsyncSession, test_user):
        task = PersonalTaskModelFactory.build(
            user_id=test_user.id, title="Important Task"
        )

        db_session.add(task)
        await db_session.commit()

        result = await repo.get_by_id_and_user(task_id=task.id, user_id=test_user.id)

        assert result is not None
        assert result.id == task.id
        assert result.title == "Important Task"

    async def test_returns_none_for_wrong_user(
        self, repo, test_user, other_user, db_session: AsyncSession
    ):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        result = await repo.get_by_id_and_user(task_id=task.id, user_id=other_user.id)

        assert result is None

    async def test_returns_none_for_nonexistent_task(
        self, repo, db_session: AsyncSession, test_user
    ):

        result = await repo.get_by_id_and_user(task_id=9999, user_id=test_user.id)

        assert result is None


class TestCreate:
    async def test_with_all_fields_success(
        self, repo, db_session: AsyncSession, test_user
    ):
        deadline = datetime.now(timezone.utc) + timedelta(days=1)
        task_data = {
            "title": "Important Task",
            "description": "Some description",
            "deadline": deadline,
            "priority": TaskPriority.HIGH,
            "status": TaskStatus.TODO,
        }

        task = await repo.create(user_id=test_user.id, data=task_data)

        db_task = await db_session.get(model.PersonalTask, task.id)

        assert task and db_task is not None
        assert task.user_id == db_task.user_id
        assert task.title == db_task.title
        assert task.description == db_task.description
        assert task.deadline == db_task.deadline
        assert task.priority == db_task.priority
        assert task.status == db_task.status

    async def test_with_minimal_fields_success(
        self, repo, db_session: AsyncSession, test_user
    ):
        task_data = {
            "title": "Important Task",
            "priority": TaskPriority.LOW,
            "status": TaskStatus.IN_PROGRESS,
        }

        task = await repo.create(user_id=test_user.id, data=task_data)

        db_task = await db_session.get(model.PersonalTask, task.id)

        assert task and db_task is not None
        assert task.user_id == db_task.user_id
        assert task.title == db_task.title
        assert task.priority == db_task.priority
        assert task.status == db_task.status
        assert db_task.description is None
        assert db_task.deadline is None


@pytest.mark.integration
class TestUpdateById:
    async def test_success(self, repo, db_session: AsyncSession, test_user):
        task = PersonalTaskModelFactory.build(
            user_id=test_user.id, title="Old Title", status=TaskStatus.IN_PROGRESS
        )
        db_session.add(task)
        await db_session.commit()

        update_data = {"title": "New Title", "status": TaskStatus.DONE}

        updated_task = await repo.update_by_id(task_id=task.id, data=update_data)

        assert updated_task.title == update_data["title"]
        assert updated_task.status == update_data["status"]


@pytest.mark.integration
class TestDeleteById:
    async def test_success(self, repo, db_session: AsyncSession, test_user):
        task = PersonalTaskModelFactory.build(user_id=test_user.id)

        db_session.add(task)
        await db_session.commit()

        await repo.delete_by_id(task_id=task.id)

        db_task = await db_session.get(model.PersonalTask, task.id)

        assert db_task is None
