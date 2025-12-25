import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException, status

from modules.projects import (
    repository,
    service as project_service,
    schemas as project_schemas,
)
from common import schemas as common_schemas
from enums.project import ProjectStatus

from tests.factories.models import ProjectModelFactory, UserModelFactory
from tests.factories.schemas import ProjectCreateFactory, ProjectPatchFactory


@pytest.fixture
def mock_repo():
    """Mock project repository"""
    return AsyncMock(spec=repository.ProjectRepository)


@pytest.fixture
def service(mock_repo):
    """Project service with mocked repository"""
    return project_service.ProjectService(repo=mock_repo)


@pytest.mark.unit
class TestCreate:
    @pytest.mark.parametrize(
        "project_data",
        [
            (ProjectCreateFactory.build()),  # All data
            (project_schemas.ProjectCreate(title="test")),  # Minimal data
        ],
    )
    async def test_success(self, service, mock_repo, project_data):
        user = UserModelFactory.build()
        created_project = ProjectModelFactory.build(
            **project_data.model_dump(exclude_unset=True)
        )

        mock_repo.create.return_value = created_project

        result = await service.create(user_id=user.id, project_data=project_data)

        assert result == created_project
        mock_repo.create.assert_called_once()

        kwargs = mock_repo.create.call_args.kwargs

        assert kwargs["user_id"] == user.id
        for key, value in project_data.model_dump(exclude_unset=True).items():
            assert kwargs["data"][key] == value


@pytest.mark.unit
class TestGetAll:
    async def test_pagination_response(self, service, mock_repo):
        user = UserModelFactory.build()
        projects = [ProjectModelFactory.build() for _ in range(10)]

        mock_repo.get_all.return_value = [projects, 10]

        filters = project_schemas.ProjectFilterParams()
        sorting = project_schemas.ProjectSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=2, size=4)

        result = await service.get_all(
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

    async def test_call_repository_with_correct_params(self, service, mock_repo):
        user = UserModelFactory.build()

        mock_repo.get_all.return_value = [[], 0]

        filters = project_schemas.ProjectFilterParams(
            status=ProjectStatus.ACTIVE, search="game"
        )
        sorting = project_schemas.ProjectSortingParams(sort_by="deadline", order="desc")
        pagination = common_schemas.BasePaginationParams(page=3, size=10)

        await service.get_all(
            user_id=user.id,
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )

        mock_repo.get_all.assert_called_once()

        kwargs = mock_repo.get_all.call_args.kwargs

        assert kwargs["user_id"] == user.id
        assert kwargs["filters"].status == filters.status
        assert kwargs["filters"].search == filters.search
        assert kwargs["sorting"].sort_by == sorting.sort_by
        assert kwargs["sorting"].order == sorting.order
        assert kwargs["pagination"].size == 10
        assert kwargs["pagination"].offset == 20

    async def test_empty_results(self, service, mock_repo):
        user = UserModelFactory.build()

        mock_repo.get_all.return_value = [[], 0]

        filters = project_schemas.ProjectFilterParams()
        sorting = project_schemas.ProjectSortingParams(sort_by="created_at")
        pagination = common_schemas.BasePaginationParams(page=1, size=10)

        result = await service.get_all(
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
class TestGetOne:
    async def test_success(self, service, mock_repo):
        project = ProjectModelFactory.build()

        mock_repo.get_by_id.return_value = project

        result = await service.get_one(project_id=project.id)

        assert result == project
        mock_repo.get_by_id.assert_called_once_with(project_id=project.id)


@pytest.mark.unit
class TestUpdate:
    @pytest.mark.parametrize(
        "update_data",
        [
            (ProjectPatchFactory.build()),  # All data
            (project_schemas.ProjectPatch(title="test", deadline=None)),  # Partial data
        ],
    )
    async def test_success(self, service, mock_repo, update_data):
        updated_project = ProjectModelFactory.build(
            **update_data.model_dump(exclude_unset=True)
        )

        mock_repo.update_by_id.return_value = updated_project

        result = await service.update(
            project_id=updated_project.id, update_data=update_data
        )

        assert result == updated_project
        mock_repo.update_by_id.assert_called_once_with(
            project_id=updated_project.id,
            data=update_data.model_dump(exclude_unset=True),
        )

    async def test_with_no_data(self, service, mock_repo):
        update_data = project_schemas.ProjectPatch()

        with pytest.raises(HTTPException) as exc_info:
            await service.update(project_id=1, update_data=update_data)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "No data to update"
        mock_repo.update_by_id.assert_not_called()


@pytest.mark.unit
class TestDelete:
    async def test_success(self, service, mock_repo):
        mock_repo.delete_by_id.return_value = None

        result = await service.delete(project_id=1)

        assert result is None
        mock_repo.delete_by_id.assert_called_once_with(project_id=1)
