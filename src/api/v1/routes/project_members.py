from fastapi import APIRouter, Depends, Response, status

from api.v1.deps.permissions import (
    require_project_permission,
)
from api.v1.deps.services import get_project_member_service
from modules.project_members import service, schemas, model as member_model

from enums.project import ProjectPermission

router = APIRouter()


@router.get(
    "",
    response_model=list[schemas.ProjectMemberRead],
    dependencies=[Depends(require_project_permission(ProjectPermission.VIEW_MEMBERS))],
)
async def get_all_project_members(
    project_id: int,
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    return await members_svc.get_all(project_id=project_id)


@router.post(
    "",
    response_model=schemas.ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: int,
    data_to_add: schemas.ProjectMemberAdd,
    actor: member_model.ProjectMember = Depends(
        require_project_permission(ProjectPermission.ADD_MEMBERS)
    ),
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    return await members_svc.add(project_id=project_id, actor=actor, data=data_to_add)


@router.patch("/{user_id}", response_model=schemas.ProjectMemberRead)
async def update_project_member(
    project_id: int,
    user_id: int,
    update_data: schemas.ProjectMemberPatch,
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
    actor: member_model.ProjectMember = Depends(
        require_project_permission(ProjectPermission.REMOVE_MEMBERS)
    ),
    members_svc: service.ProjectMemberService = Depends(get_project_member_service),
):
    await members_svc.delete(project_id=project_id, user_id=user_id, actor=actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
