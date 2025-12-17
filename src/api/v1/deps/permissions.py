from fastapi import Depends, HTTPException, status

from api.v1.deps.auth import get_current_user
from api.v1.deps.repositories import get_project_member_repository
from modules.users import model as user_model
from modules.project_members import (
    repository as member_repository,
    model as member_model,
)
from core.security.permissions import PermissionChecker
from enums.project import ProjectPermission


async def get_current_project_member(
    project_id: int,
    user: user_model.User = Depends(get_current_user),
    member_repo: member_repository.ProjectMemberRepository = Depends(
        get_project_member_repository
    ),
) -> member_model.ProjectMember:
    """Get current member in project."""

    member = await member_repo.get_by_user_id_and_project_id(
        user_id=user.id, project_id=project_id
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    return member


def require_project_permission(required_permission: ProjectPermission):
    """Factory that creates a dependency to check project permissions."""

    async def check_permission(
        member: member_model.ProjectMember = Depends(get_current_project_member),
    ) -> member_model.ProjectMember:
        PermissionChecker.require_permission(member.role, required_permission)

        return member

    return check_permission
