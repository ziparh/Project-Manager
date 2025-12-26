from fastapi import APIRouter, Depends, Response, status

from api.v1.deps.auth import get_current_user
from api.v1.deps.personal_tasks import get_current_personal_task
from api.v1.deps.services import get_personal_tasks_service
from modules.users.model import User as UserModel
from modules.personal_tasks import (
    schemas as tasks_schema,
    service as tasks_service,
    model,
)
from common import schemas as common_schemas

router = APIRouter()


@router.get(
    "",
    response_model=common_schemas.BasePaginationResponse[tasks_schema.PersonalTaskRead],
)
async def get_list_of_personal_tasks(
    # Query params
    filters: tasks_schema.PersonalTaskFilterParams = Depends(),
    sorting: tasks_schema.PersonalTaskSortingParams = Depends(),
    pagination: common_schemas.BasePaginationParams = Depends(),
    # Other
    user: UserModel = Depends(get_current_user),
    tasks_svc: tasks_service.PersonalTaskService = Depends(get_personal_tasks_service),
):
    return await tasks_svc.get_list(
        user_id=user.id, filters=filters, sorting=sorting, pagination=pagination
    )


@router.post(
    "",
    response_model=tasks_schema.PersonalTaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_personal_task(
    task_data: tasks_schema.PersonalTaskCreate,
    user: UserModel = Depends(get_current_user),
    tasks_svc: tasks_service.PersonalTaskService = Depends(get_personal_tasks_service),
):
    return await tasks_svc.create(user_id=user.id, data=task_data)


@router.get("/{task_id}", response_model=tasks_schema.PersonalTaskRead)
async def get_personal_task(
    task: model.PersonalTask = Depends(get_current_personal_task),
):
    return task


@router.patch("/{task_id}", response_model=tasks_schema.PersonalTaskRead)
async def patch_personal_task(
    update_data: tasks_schema.PersonalTaskPatch,
    task: model.PersonalTask = Depends(get_current_personal_task),
    tasks_svc: tasks_service.PersonalTaskService = Depends(get_personal_tasks_service),
):
    return await tasks_svc.update(task=task, data=update_data)


@router.delete("/{task_id}")
async def delete_personal_task(
    task: model.PersonalTask = Depends(get_current_personal_task),
    tasks_svc: tasks_service.PersonalTaskService = Depends(get_personal_tasks_service),
):
    await tasks_svc.delete(task=task)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
