from fastapi import APIRouter, Depends, Response, status

from api.v1.deps.services import get_project_tasks_service
from api.v1.deps.permissions import (
    require_project_permission,
    get_current_project_member,
)
from api.v1.deps.project_tasks import (
    get_current_project_task,
    get_current_project_open_task,
)
from modules.project_tasks import schemas
from modules.project_tasks.service import ProjectTaskService
from modules.project_tasks.model import ProjectTask as ProjectTaskModel
from modules.project_members.model import ProjectMember as ProjectMemberModel
from common.schemas import BasePaginationResponse, BasePaginationParams
from enums.project import ProjectPermission

router = APIRouter()


@router.get(
    "",
    response_model=BasePaginationResponse[schemas.ProjectTaskRead],
    dependencies=[Depends(require_project_permission(ProjectPermission.VIEW_TASKS))],
)
async def get_all_project_tasks(
    # Other
    project_id: int,
    service: ProjectTaskService = Depends(get_project_tasks_service),
    # Query params
    filters: schemas.ProjectTasksFiltersParams = Depends(),
    sorting: schemas.ProjectTasksSortingParams = Depends(),
    pagination: BasePaginationParams = Depends(),
):
    return await service.get_all(
        project_id=project_id,
        filters=filters,
        sorting=sorting,
        pagination=pagination,
    )


@router.post(
    "",
    response_model=schemas.ProjectTaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project_task(
    project_id: int,
    task_data: schemas.ProjectTaskCreate,
    actor: ProjectMemberModel = Depends(
        require_project_permission(ProjectPermission.ADD_TASKS)
    ),
    service: ProjectTaskService = Depends(get_project_tasks_service),
):
    return await service.create(project_id=project_id, actor=actor, task_data=task_data)


@router.get(
    "/{task_id}",
    response_model=schemas.ProjectTaskRead,
    dependencies=[Depends(require_project_permission(ProjectPermission.VIEW_TASKS))],
)
async def get_project_task(task: ProjectTaskModel = Depends(get_current_project_task)):
    return task


@router.patch(
    "/{task_id}",
    response_model=schemas.ProjectTaskRead,
)
async def update_project_task(
    project_id: int,
    update_data: schemas.ProjectTaskPatch,
    task: ProjectTaskModel = Depends(get_current_project_task),
    actor: ProjectMemberModel = Depends(get_current_project_member),
    service: ProjectTaskService = Depends(get_project_tasks_service),
):
    return await service.update(
        project_id=project_id,
        task=task,
        actor=actor,
        update_data=update_data,
    )


@router.delete(
    "/{task_id}",
    dependencies=[Depends(require_project_permission(ProjectPermission.REMOVE_TASKS))],
)
async def remove_project_task(
    task: ProjectTaskModel = Depends(get_current_project_task),
    service: ProjectTaskService = Depends(get_project_tasks_service),
):
    await service.delete(task=task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{task_id}/assign", response_model=schemas.ProjectTaskRead)
async def assign_project_task(
    task: ProjectTaskModel = Depends(get_current_project_open_task),
    actor: ProjectMemberModel = Depends(
        require_project_permission(ProjectPermission.ASSIGN_OPEN_TASK)
    ),
    service: ProjectTaskService = Depends(get_project_tasks_service),
):
    return await service.assign(task=task, actor=actor)


@router.delete("/{task_id}/assign", response_model=schemas.ProjectTaskRead)
async def unassign_project_task(
    task: ProjectTaskModel = Depends(get_current_project_open_task),
    actor: ProjectMemberModel = Depends(
        require_project_permission(ProjectPermission.UNASSIGN_OPEN_TASK)
    ),
    service: ProjectTaskService = Depends(get_project_tasks_service),
):
    return await service.unassign(task=task, actor=actor)
