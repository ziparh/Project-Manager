from fastapi import HTTPException, status

from . import model, repository, schemas as tasks_schemas, dto as tasks_dto
from common import schemas as common_schemas, dto as common_dto


class PersonalTaskService:
    def __init__(self, repo: repository.PersonalTaskRepository):
        self.repo = repo

    async def get_list(
        self,
        user_id: int,
        filters: tasks_schemas.PersonalTaskFilterParams,
        sorting: tasks_schemas.PersonalTaskSortingParams,
        pagination: common_schemas.BasePaginationParams,
    ) -> common_schemas.BasePaginationResponse[tasks_schemas.PersonalTaskRead]:

        filter_dto = tasks_dto.PersonalTaskFilterDto(
            **filters.model_dump(exclude_unset=True)
        )
        sorting_dto = common_dto.SortingDto(**sorting.model_dump(exclude_unset=True))
        pagination_dto = common_dto.PaginationDto(
            size=pagination.size,
            offset=pagination.offset,
        )

        items, total = await self.repo.get_list(
            user_id=user_id,
            filters=filter_dto,
            sorting=sorting_dto,
            pagination=pagination_dto,
        )

        return common_schemas.BasePaginationResponse(
            items=items,
            pagination=common_schemas.BasePaginationMeta(
                total=total,
                page=pagination.page,
                size=pagination.size,
            ),
        )

    async def create(
        self, user_id: int, data: tasks_schemas.PersonalTaskCreate
    ) -> model.PersonalTask:
        task_dict = data.model_dump(exclude_unset=True)

        task = await self.repo.create(user_id=user_id, data=task_dict)

        return task

    async def update(
        self, task: model.PersonalTask, data: tasks_schemas.PersonalTaskPatch
    ) -> model.PersonalTask:
        task_dict = data.model_dump(exclude_unset=True)

        if not task_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update"
            )

        updated_task = await self.repo.update_by_id(task_id=task.id, data=task_dict)

        return updated_task

    async def delete(self, task: model.PersonalTask) -> None:
        await self.repo.delete_by_id(task.id)
