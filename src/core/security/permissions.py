from fastapi import HTTPException, status

from enums.project import ProjectRole, ProjectPermission


class PermissionChecker:
    PERMISSIONS_MAPPING: dict[ProjectRole, set[ProjectPermission]] = {
        ProjectRole.OWNER: {
            ProjectPermission.VIEW_PROJECT,
            ProjectPermission.UPDATE_PROJECT,
            ProjectPermission.DELETE_PROJECT,
            ProjectPermission.VIEW_MEMBERS,
            ProjectPermission.ADD_MEMBERS,
            ProjectPermission.UPDATE_MEMBERS,
            ProjectPermission.REMOVE_MEMBERS,
        },
        ProjectRole.ADMIN: {
            ProjectPermission.VIEW_PROJECT,
            ProjectPermission.UPDATE_PROJECT,
            ProjectPermission.VIEW_MEMBERS,
            ProjectPermission.ADD_MEMBERS,
            ProjectPermission.UPDATE_MEMBERS,
            ProjectPermission.REMOVE_MEMBERS,
        },
        ProjectRole.MEMBER: {
            ProjectPermission.VIEW_PROJECT,
            ProjectPermission.VIEW_MEMBERS,
        },
    }

    @classmethod
    def has_permission(cls, role: ProjectRole, permission: ProjectPermission) -> bool:
        """Checking if a role has permissions."""
        return permission in cls.PERMISSIONS_MAPPING.get(role, set())

    @classmethod
    def require_permission(
        cls, role: ProjectRole, permission: ProjectPermission
    ) -> None:
        """Raise HTTPException if role doesn't have permission."""
        if not cls.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have such permission.",
            )

    @classmethod
    def can_modify_member(
        cls, actor_role: ProjectRole, target_role: ProjectRole
    ) -> bool:
        """
        Can 'actor' change/delete 'target'

        Rules:
         - Owner can modify admins and members
         - Admin can modify only members
         - Member cannot modify anyone
        """

        # Owner can modify admins and members
        if actor_role == ProjectRole.OWNER:
            return target_role in {ProjectRole.ADMIN, ProjectRole.MEMBER}

        # Admin can modify only member
        if actor_role == ProjectRole.ADMIN:
            return target_role in {ProjectRole.MEMBER}

        # Member cannot modify anyone
        return False

    @classmethod
    def can_assign_role(cls, actor_role: ProjectRole, new_role: ProjectRole) -> bool:
        """
        Can 'actor' assign 'new_role' to other member

        Rules:
         - The owner role cannot be assigned
         - Owner can assign admin and member roles
         - Admin can only assign member roles
         - Member role cannot assign roles
        """

        # The owner role cannot be assigned
        if new_role == ProjectRole.OWNER:
            return False

        # Owner can assign admin and member roles
        if actor_role == ProjectRole.OWNER:
            return new_role in {ProjectRole.ADMIN, ProjectRole.MEMBER}

        # Admin can only assign member roles
        if actor_role == ProjectRole.ADMIN:
            return new_role in {ProjectRole.MEMBER}

        # Member role cannot assign roles
        return False

    @classmethod
    def validate_member_operation(
        cls,
        actor_role: ProjectRole,
        target_role: ProjectRole,
        operation: str = "modify",
    ):
        """
        Validate method 'can_modify_member'
        Raise HTTPException if modify is forbidden
        """
        if not cls.can_modify_member(actor_role, target_role):
            if target_role == ProjectRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify project owner.",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{actor_role.value} cannot {operation} {target_role.value}.",
            )

    @classmethod
    def validate_role_assignment(cls, actor_role: ProjectRole, new_role: ProjectRole):
        """
        Validate method 'can_assign_role'
        Raise HTTPException if assigment is forbidden
        """
        if not cls.can_assign_role(actor_role, new_role):
            if new_role == ProjectRole.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot assign owner role.",
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{actor_role.value} cannot assign {new_role.value} role.",
            )
