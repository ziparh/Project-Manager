from fastapi import APIRouter, Depends, Response, status

from api.v1.deps.permissions import (
    require_project_permission,
    get_current_project_member,
)
from api.v1.deps.services import get_project_member_service
from modules.project_members import (
    service,
    schemas as member_schemas,
    model as member_model,
)
from common import schemas as common_schemas
from enums.project import ProjectPermission

router = APIRouter()


@router.get(
    "",
    response_model=common_schemas.BasePaginationResponse[
        member_schemas.ProjectMemberRead
    ],
    dependencies=[Depends(require_project_permission(ProjectPermission.VIEW_MEMBERS))],
)
async def get_all_project_members(
    # Other
    project_id: int,
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
    # Query params
    filters: member_schemas.ProjectMemberFilterParams = Depends(),
    sorting: member_schemas.ProjectMemberSortingParams = Depends(),
    pagination: common_schemas.BasePaginationParams = Depends(),
):
    return await members_svc.get_all(
        project_id=project_id,
        filters=filters,
        sorting=sorting,
        pagination=pagination,
    )


@router.post(
    "",
    response_model=member_schemas.ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: int,
    data_to_add: member_schemas.ProjectMemberAdd,
    actor: member_model.ProjectMember = Depends(
        require_project_permission(ProjectPermission.ADD_MEMBERS)
    ),
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    return await members_svc.add(project_id=project_id, actor=actor, data=data_to_add)


@router.patch("/{user_id}", response_model=member_schemas.ProjectMemberRead)
async def update_project_member(
    project_id: int,
    user_id: int,
    update_data: member_schemas.ProjectMemberPatch,
    actor: member_model.ProjectMember = Depends(
        require_project_permission(ProjectPermission.UPDATE_MEMBERS)
    ),
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    return await members_svc.update(
        project_id=project_id,
        user_id=user_id,
        actor=actor,
        update_data=update_data,
    )


@router.delete("/{user_id}")
async def remove_project_member(
    project_id: int,
    user_id: int,
    actor: member_model.ProjectMember = Depends(get_current_project_member),
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    await members_svc.delete(project_id=project_id, user_id=user_id, actor=actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
