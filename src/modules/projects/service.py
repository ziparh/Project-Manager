from fastapi import HTTPException, status

from . import model, repository, schemas as project_schemas, dto as project_dto
from common import schemas as common_schema, dto as common_dto


class ProjectService:
    def __init__(self, repo: repository.ProjectRepository):
        self.repo = repo

    async def create(
        self, user_id: int, project_data: project_schemas.ProjectCreate
    ) -> model.Project:
        project_dict = project_data.model_dump(exclude_unset=True)

        project = await self.repo.create(user_id=user_id, data=project_dict)

        return project

    async def get_all(
        self,
        user_id: int,
        filters: project_schemas.ProjectFilterParams,
        sorting: project_schemas.ProjectSortingParams,
        pagination: common_schema.BasePaginationParams,
    ) -> common_schema.BasePaginationResponse[project_schemas.ProjectRead]:

        filters_dto = project_dto.ProjectFilterDto(
            **filters.model_dump(exclude_unset=True)
        )
        sorting_dto = common_dto.SortingDto(**sorting.model_dump(exclude_unset=True))
        pagination_dto = common_dto.PaginationDto(
            offset=pagination.offset, size=pagination.size
        )

        items, total = await self.repo.get_all(
            user_id=user_id,
            filters=filters_dto,
            sorting=sorting_dto,
            pagination=pagination_dto,
        )

        return common_schema.BasePaginationResponse(
            items=items,
            pagination=common_schema.BasePaginationMeta(
                total=total,
                page=pagination.page,
                size=pagination.size,
            ),
        )

    async def get_one(self, project_id: int) -> model.Project:
        return await self.repo.get_by_id(project_id=project_id)

    async def update(
        self, project_id: int, update_data: project_schemas.ProjectPatch
    ) -> model.Project:
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update"
            )

        updated_project = await self.repo.update_by_id(
            project_id=project_id, data=update_dict
        )

        return updated_project

    async def delete(self, project_id: int) -> None:
        await self.repo.delete_by_id(project_id=project_id)
