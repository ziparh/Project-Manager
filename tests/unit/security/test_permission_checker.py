import pytest
from fastapi import HTTPException, status

from core.security.permissions import PermissionChecker
from enums.project import ProjectRole, ProjectPermission


@pytest.mark.unit
class TestHasPermissions:
    @pytest.mark.parametrize(
        "role, permission, expected_result",
        [
            # OWNER permissions
            (ProjectRole.OWNER, ProjectPermission.VIEW_PROJECT, True),
            (ProjectRole.OWNER, ProjectPermission.UPDATE_PROJECT, True),
            (ProjectRole.OWNER, ProjectPermission.DELETE_PROJECT, True),
            (ProjectRole.OWNER, ProjectPermission.VIEW_MEMBERS, True),
            (ProjectRole.OWNER, ProjectPermission.ADD_MEMBERS, True),
            (ProjectRole.OWNER, ProjectPermission.UPDATE_MEMBERS, True),
            (ProjectRole.OWNER, ProjectPermission.REMOVE_MEMBERS, True),
            # ADMIN permissions
            (ProjectRole.ADMIN, ProjectPermission.VIEW_PROJECT, True),
            (ProjectRole.ADMIN, ProjectPermission.UPDATE_PROJECT, True),
            (ProjectRole.ADMIN, ProjectPermission.DELETE_PROJECT, False),
            (ProjectRole.ADMIN, ProjectPermission.VIEW_MEMBERS, True),
            (ProjectRole.ADMIN, ProjectPermission.ADD_MEMBERS, True),
            (ProjectRole.ADMIN, ProjectPermission.UPDATE_MEMBERS, True),
            (ProjectRole.ADMIN, ProjectPermission.REMOVE_MEMBERS, True),
            # MEMBER permissions
            (ProjectRole.MEMBER, ProjectPermission.VIEW_PROJECT, True),
            (ProjectRole.MEMBER, ProjectPermission.UPDATE_PROJECT, False),
            (ProjectRole.MEMBER, ProjectPermission.DELETE_PROJECT, False),
            (ProjectRole.MEMBER, ProjectPermission.VIEW_MEMBERS, True),
            (ProjectRole.MEMBER, ProjectPermission.ADD_MEMBERS, False),
            (ProjectRole.MEMBER, ProjectPermission.UPDATE_MEMBERS, False),
            (ProjectRole.MEMBER, ProjectPermission.REMOVE_MEMBERS, False),
        ],
    )
    def test_success(self, role, permission, expected_result):
        assert PermissionChecker.has_permission(role, permission) == expected_result


@pytest.mark.unit
class TestRequirePermission:
    def test_success(self):
        PermissionChecker.require_permission(
            ProjectRole.OWNER, ProjectPermission.DELETE_PROJECT
        )

    def test_invalid_permission(self):
        with pytest.raises(HTTPException) as exc_info:
            PermissionChecker.require_permission(
                ProjectRole.ADMIN, ProjectPermission.DELETE_PROJECT
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "You don't have such permission."


@pytest.mark.unit
class TestCanModifyMember:
    @pytest.mark.parametrize(
        "actor_role, target_role, expected_result",
        [
            # If OWNER modify
            (ProjectRole.OWNER, ProjectRole.OWNER, False),
            (ProjectRole.OWNER, ProjectRole.ADMIN, True),
            (ProjectRole.OWNER, ProjectRole.MEMBER, True),
            # If ADMIN modify
            (ProjectRole.ADMIN, ProjectRole.OWNER, False),
            (ProjectRole.ADMIN, ProjectRole.ADMIN, False),
            (ProjectRole.ADMIN, ProjectRole.MEMBER, True),
            # If MEMBER modify
            (ProjectRole.MEMBER, ProjectRole.OWNER, False),
            (ProjectRole.MEMBER, ProjectRole.ADMIN, False),
            (ProjectRole.MEMBER, ProjectRole.MEMBER, False),
        ],
    )
    def test_success(self, actor_role, target_role, expected_result):
        assert (
            PermissionChecker.can_modify_member(actor_role, target_role)
            == expected_result
        )


@pytest.mark.unit
class TestCanAssignRole:
    @pytest.mark.parametrize(
        "actor_role, new_role, expected_result",
        [
            # If OWNER assign
            (ProjectRole.OWNER, ProjectRole.OWNER, False),
            (ProjectRole.OWNER, ProjectRole.ADMIN, True),
            (ProjectRole.OWNER, ProjectRole.MEMBER, True),
            # If ADMIN assign
            (ProjectRole.ADMIN, ProjectRole.OWNER, False),
            (ProjectRole.ADMIN, ProjectRole.ADMIN, False),
            (ProjectRole.ADMIN, ProjectRole.MEMBER, True),
            # If MEMBER assign
            (ProjectRole.MEMBER, ProjectRole.OWNER, False),
            (ProjectRole.MEMBER, ProjectRole.ADMIN, False),
            (ProjectRole.MEMBER, ProjectRole.MEMBER, False),
        ],
    )
    def test_success(self, actor_role, new_role, expected_result):
        assert (
            PermissionChecker.can_assign_role(actor_role, new_role) == expected_result
        )


@pytest.mark.unit
class TestValidateMemberOperation:
    def test_success(self):
        PermissionChecker.validate_member_operation(
            actor_role=ProjectRole.OWNER,
            target_role=ProjectRole.ADMIN,
        )

    def test_cannot_modify_owner(self):
        with pytest.raises(HTTPException) as exc_info:
            PermissionChecker.validate_member_operation(
                actor_role=ProjectRole.ADMIN,
                target_role=ProjectRole.OWNER,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Cannot modify project owner"

    def test_cannot_modify(self):
        with pytest.raises(HTTPException) as exc_info:
            PermissionChecker.validate_member_operation(
                actor_role=ProjectRole.ADMIN,
                target_role=ProjectRole.ADMIN,
                operation="remove",
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "admin cannot remove admin"


@pytest.mark.unit
class TestValidateRoleAssigment:
    def test_success(self):
        PermissionChecker.validate_role_assignment(
            actor_role=ProjectRole.OWNER,
            new_role=ProjectRole.ADMIN,
        )

    def test_cannot_assign_owner_role(self):
        with pytest.raises(HTTPException) as exc_info:
            PermissionChecker.validate_role_assignment(
                actor_role=ProjectRole.OWNER,
                new_role=ProjectRole.OWNER,
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Cannot assign owner role"
