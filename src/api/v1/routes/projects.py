from fastapi import APIRouter, Depends, Response, status

from api.v1.deps.auth import get_current_user
from api.v1.deps.permissions import require_project_permission
from api.v1.deps.services import get_projects_service
from modules.projects import schemas as project_schemas, service
from modules.users import model as user_model
from common import schemas as common_schemas
from enums.project import ProjectPermission

router = APIRouter()


@router.get(
    "",
    response_model=common_schemas.BasePaginationResponse[project_schemas.ProjectRead],
)
async def get_user_projects(
    # Query params
    filters: project_schemas.ProjectFilterParams = Depends(),
    sorting: project_schemas.ProjectSortingParams = Depends(),
    pagination: common_schemas.BasePaginationParams = Depends(),
    # Other
    user: user_model.User = Depends(get_current_user),
    project_svc: service.ProjectService = Depends(get_projects_service),
):
    return await project_svc.get_all(
        user_id=user.id,
        filters=filters,
        sorting=sorting,
        pagination=pagination,
    )


@router.post(
    "", response_model=project_schemas.ProjectRead, status_code=status.HTTP_201_CREATED
)
async def create_project(
    project_data: project_schemas.ProjectCreate,
    user: user_model.User = Depends(get_current_user),
    project_svc: service.ProjectService = Depends(get_projects_service),
):
    return await project_svc.create(user_id=user.id, project_data=project_data)


@router.get(
    "/{project_id}",
    response_model=project_schemas.ProjectRead,
    dependencies=[Depends(require_project_permission(ProjectPermission.VIEW_PROJECT))],
)
async def get_project(
    project_id: int,
    project_svc: service.ProjectService = Depends(get_projects_service),
):
    return await project_svc.get_one(project_id=project_id)


@router.patch(
    "/{project_id}",
    response_model=project_schemas.ProjectRead,
    dependencies=[
        Depends(require_project_permission(ProjectPermission.UPDATE_PROJECT))
    ],
)
async def update_project(
    project_id: int,
    update_data: project_schemas.ProjectPatch,
    project_svc: service.ProjectService = Depends(get_projects_service),
):
    return await project_svc.update(
        project_id=project_id,
        update_data=update_data,
    )


@router.delete(
    "/{project_id}",
    dependencies=[
        Depends(require_project_permission(ProjectPermission.DELETE_PROJECT))
    ],
)
async def delete_project(
    project_id: int, project_svc: service.ProjectService = Depends(get_projects_service)
):
    await project_svc.delete(project_id=project_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
