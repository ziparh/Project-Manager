import pytest
import time_machine
from unittest.mock import AsyncMock
from datetime import datetime, timedelta, timezone

from modules.personal_tasks import (
    repository,
    service as tasks_service,
    schemas as tasks_schemas,
)
from common import schemas as common_schemas
from enums.task import TaskStatus, TaskPriority

from tests.factories.models import UserModelFactory, PersonalTaskModelFactory


@pytest.fixture
def mock_repo():
    """Mock personal task repository"""
    return AsyncMock(spec=repository.PersonalTaskRepository)


@pytest.fixture
def service(mock_repo):
    """Personal task service with mocked repository"""
    return tasks_service.PersonalTaskService(repo=mock_repo)


@pytest.mark.unit
class TestGetList:
    async def test_paginated_response(self, service, mock_repo):
        user = UserModelFactory.build()
        tasks = [PersonalTaskModelFactory.build() for _ in range(10)]

        mock_repo.get_list.return_value = [tasks, 10]

        filters = tasks_schemas.PersonalTaskFilterParams()
        sorting = tasks_schemas.PersonalTaskSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=2, size=4)

        result = await service.get_list(
            user_id=user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert isinstance(result, common_schemas.BasePaginationResponse)
        assert len(result.items) == 10
        assert result.pagination.total == 10
        assert result.pagination.page == 2
        assert result.pagination.size == 4
        assert result.pagination.pages == 3
        assert result.pagination.has_next
        assert result.pagination.has_previous

    async def test_calls_repository_with_correct_params(self, service, mock_repo):
        user = UserModelFactory.build()

        mock_repo.get_list.return_value = [[], 0]

        filters = tasks_schemas.PersonalTaskFilterParams(
            status=TaskStatus.IN_PROGRESS, search="meeting"
        )
        sorting = tasks_schemas.PersonalTaskSortingParams(
            sort_by="deadline", order="desc"
        )
        pagination = common_schemas.BasePaginationParams(page=2, size=10)

        await service.get_list(
            user_id=user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        mock_repo.get_list.assert_called_once()
        kwargs = mock_repo.get_list.call_args.kwargs

        assert kwargs["user_id"] == user.id
        assert kwargs["filters"].status == TaskStatus.IN_PROGRESS
        assert kwargs["filters"].search == "meeting"
        assert kwargs["sorting"].sort_by == "deadline"
        assert kwargs["sorting"].order == "desc"
        assert kwargs["pagination"].size == 10
        assert kwargs["pagination"].offset == 10

    async def test_empty_result(self, service, mock_repo):
        user = UserModelFactory.build()

        mock_repo.get_list.return_value = ([], 0)

        filters = tasks_schemas.PersonalTaskFilterParams()
        sorting = tasks_schemas.PersonalTaskSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=1, size=10)

        result = await service.get_list(
            user_id=user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        assert len(result.items) == 0
        assert result.pagination.total == 0
        assert result.pagination.page == 1
        assert result.pagination.size == 10
        assert result.pagination.pages == 1
        assert not result.pagination.has_next
        assert not result.pagination.has_previous


@pytest.mark.unit
class TestCreate:
    async def test_with_all_data(self, service, mock_repo):
        user = UserModelFactory.build()
        task_data = tasks_schemas.PersonalTaskCreate(
            title="Test task",
            description="Some description",
            deadline=datetime.now(timezone.utc),
            priority=TaskPriority.LOW,
            status=TaskStatus.TODO,
        )
        created_task = PersonalTaskModelFactory.build(
            user_id=user.id,
            title=task_data.title,
            description=task_data.description,
            deadline=task_data.deadline,
            priority=task_data.priority,
            status=task_data.status,
        )

        mock_repo.create.return_value = created_task

        result = await service.create(user_id=user.id, data=task_data)

        assert result == created_task
        mock_repo.create.assert_called_once()

        kwargs = mock_repo.create.call_args.kwargs
        assert kwargs["user_id"] == user.id
        assert kwargs["data"]["title"] == "Test task"
        assert kwargs["data"]["description"] == "Some description"
        assert kwargs["data"]["deadline"] == task_data.deadline
        assert kwargs["data"]["priority"] == task_data.priority
        assert kwargs["data"]["status"] == task_data.status

    async def test_with_minimal_data(self, service, mock_repo):
        user = UserModelFactory.build()
        task_data = tasks_schemas.PersonalTaskCreate(title="Test task")
        created_task = PersonalTaskModelFactory.build(
            user_id=user.id, title=task_data.title
        )

        mock_repo.create.return_value = created_task

        result = await service.create(user_id=user.id, data=task_data)

        assert result == created_task
        mock_repo.create.assert_called_once()

        kwargs = mock_repo.create.call_args.kwargs
        assert kwargs["user_id"] == user.id
        assert kwargs["data"]["title"] == "Test task"


@pytest.mark.unit
class TestUpdate:
    async def test_with_all_data(self, service, mock_repo):
        user = UserModelFactory.build()
        fixed_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with time_machine.travel(fixed_dt, tick=False):
            existing_task = PersonalTaskModelFactory.build(
                user_id=user.id,
                title="Old title",
                description="Some old description",
                deadline=datetime.now(timezone.utc) + timedelta(days=1),
                priority=TaskPriority.LOW,
                status=TaskStatus.TODO,
            )
            update_data = tasks_schemas.PersonalTaskPatch(
                title="New title",
                description="Some new description",
                deadline=datetime.now(timezone.utc) + timedelta(days=2),
                priority=TaskPriority.CRITICAL,
                status=TaskStatus.IN_PROGRESS,
            )
            updated_task = PersonalTaskModelFactory.build(
                id=existing_task.id,
                user_id=user.id,
                title=update_data.title,
                description=update_data.description,
                deadline=update_data.deadline,
                priority=update_data.priority,
                status=update_data.status,
            )

            mock_repo.update_by_id.return_value = updated_task

            result = await service.update(
                task=existing_task,
                data=update_data,
            )

            assert result == updated_task
            mock_repo.update_by_id.assert_called_once()

            kwargs = mock_repo.update_by_id.call_args.kwargs
            assert kwargs["task_id"] == existing_task.id
            assert kwargs["data"]["title"] == "New title"
            assert kwargs["data"]["description"] == "Some new description"
            assert kwargs["data"]["deadline"] == datetime.now(timezone.utc) + timedelta(
                days=2
            )
            assert kwargs["data"]["status"] == TaskStatus.IN_PROGRESS
            assert kwargs["data"]["priority"] == TaskPriority.CRITICAL

    async def test_with_partial_data(self, service, mock_repo):
        user = UserModelFactory.build()
        existing_task = PersonalTaskModelFactory.build(
            user_id=user.id,
            title="Old title",
            status=TaskStatus.TODO,
            priority=TaskPriority.CRITICAL,
        )
        update_data = tasks_schemas.PersonalTaskPatch(
            title="New title", status=TaskStatus.IN_PROGRESS
        )
        updated_task = PersonalTaskModelFactory.build(
            id=existing_task.id,
            user_id=user.id,
            title=update_data.title,
            status=update_data.status,
        )

        mock_repo.update_by_id.return_value = updated_task

        result = await service.update(
            task=existing_task,
            data=update_data,
        )

        assert result == updated_task
        mock_repo.update_by_id.assert_called_once()

        kwargs = mock_repo.update_by_id.call_args.kwargs
        assert kwargs["task_id"] == existing_task.id
        assert kwargs["data"]["title"] == "New title"
        assert kwargs["data"]["status"] == TaskStatus.IN_PROGRESS


@pytest.mark.unit
class TestDelete:
    async def test_success(self, service, mock_repo):
        user = UserModelFactory.build()
        task = PersonalTaskModelFactory.build(user_id=user.id)

        mock_repo.delete_by_id.return_value = None

        await service.delete(task=task)

        mock_repo.delete_by_id.assert_called_once_with(task.id)
