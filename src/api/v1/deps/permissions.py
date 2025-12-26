from fastapi import Depends

from api.v1.deps.project_members import get_current_project_member
from modules.project_members.model import ProjectMember as ProjectMemberModel
from core.security.permissions import PermissionChecker
from enums.project import ProjectPermission


def require_project_permission(required_permission: ProjectPermission):
    """Factory that creates a dependency to check project permissions."""

    async def check_permission(
        member: ProjectMemberModel = Depends(get_current_project_member),
    ) -> ProjectMemberModel:
        PermissionChecker.require_permission(member.role, required_permission)

        return member

    return check_permission
