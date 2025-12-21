from typing import Sequence
from fastapi import HTTPException, status

from core.security.permissions import PermissionChecker
from . import repository as member_repository, model, schemas as member_schemas, dto as member_dto
from modules.users import repository as user_repository
from common import schemas as common_schemas, dto as common_dto
from utils.datetime import utc_now
from enums.project import ProjectRole


class ProjectMemberService:
    def __init__(
        self,
        member_repo: member_repository.ProjectMemberRepository,
        user_repo: user_repository.UserRepository,
    ):
        self.member_repo = member_repo
        self.user_repo = user_repo

    async def get_all(
            self,
            project_id: int,
            filters: member_schemas.ProjectMemberFilterParams,
            sorting: member_schemas.ProjectMemberSortingParams,
            pagination: common_schemas.BasePaginationParams
    ) -> common_schemas.BasePaginationResponse[member_schemas.ProjectMemberRead]:
        filters_dto = member_dto.ProjectMemberFilterDto(
            **filters.model_dump(exclude_unset=True)
        )
        sorting_dto = common_dto.SortingDto(
            **sorting.model_dump(exclude_unset=True)
        )
        pagination_dto = common_dto.PaginationDto(
            offset=pagination.offset, size=pagination.size
        )

        items, total = await self.member_repo.get_all(
            project_id=project_id,
            filters=filters_dto,
            sorting=sorting_dto,
            pagination=pagination_dto,
        )

        return common_schemas.BasePaginationResponse(
            items=items,
            pagination=common_schemas.BasePaginationMeta(
                total=total,
                page=pagination.page,
                size=pagination.size,
            )
        )

    async def add(
        self,
        project_id: int,
        actor: model.ProjectMember,
        data: member_schemas.ProjectMemberAdd,
    ) -> model.ProjectMember:
        PermissionChecker.validate_role_assignment(
            actor_role=actor.role, new_role=data.role
        )

        is_user = await self.user_repo.get_by_id(data.user_id)
        if not is_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        is_member = await self.member_repo.get_by_user_id_and_project_id(
            user_id=data.user_id, project_id=project_id
        )
        if is_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a project member",
            )

        created_member = await self.member_repo.create(
            project_id=project_id,
            user_id=data.user_id,
            role=data.role,
            joined_at=utc_now(),
        )

        return created_member

    async def update(
        self,
        project_id: int,
        user_id: int,
        actor: model.ProjectMember,
        update_data: member_schemas.ProjectMemberPatch,
    ) -> model.ProjectMember:
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update"
            )

        membership = await self.member_repo.get_by_user_id_and_project_id(
            user_id=user_id, project_id=project_id
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )

        PermissionChecker.validate_member_operation(
            actor_role=actor.role, target_role=membership.role, operation="update"
        )
        PermissionChecker.validate_role_assignment(
            actor_role=actor.role, new_role=update_dict["role"]
        )
        return await self.member_repo.update_by_membership(
            membership=membership, data=update_dict
        )

    async def delete(
        self, project_id: int, user_id: int, actor: model.ProjectMember
    ) -> None:
        membership = await self.member_repo.get_by_user_id_and_project_id(
            user_id=user_id, project_id=project_id
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
            )

        if membership.role == ProjectRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove project owner",
            )

        # If user delete themselves, it is allowed (except for owner)
        if actor.user_id == user_id:
            await self.member_repo.delete_by_membership(membership)
            return

        # If user delete someone else, check the permission
        PermissionChecker.validate_member_operation(
            actor_role=actor.role, target_role=membership.role, operation="delete"
        )

        await self.member_repo.delete_by_membership(membership=membership)
