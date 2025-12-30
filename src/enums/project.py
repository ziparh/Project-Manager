from enum import Enum


class ProjectStatus(Enum):
    PLANNING = "planning"
    ON_HOLD = "on_hold"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @property
    def sort_order(self) -> int:
        match self:
            case ProjectStatus.CANCELLED:
                return 5
            case ProjectStatus.COMPLETED:
                return 4
            case ProjectStatus.ACTIVE:
                return 3
            case ProjectStatus.ON_HOLD:
                return 2
            case ProjectStatus.PLANNING:
                return 1


class ProjectRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    @property
    def sort_order(self) -> int:
        match self:
            case ProjectRole.OWNER:
                return 3
            case ProjectRole.ADMIN:
                return 2
            case ProjectRole.MEMBER:
                return 1


class ProjectPermission(Enum):
    """Permissions for project operations."""

    # Project permissions
    VIEW_PROJECT = "view_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"

    # Member permissions
    VIEW_MEMBERS = "view_members"
    ADD_MEMBERS = "add_members"
    UPDATE_MEMBERS = "update_members"
    REMOVE_MEMBERS = "remove_members"

    # Task permissions
    VIEW_TASKS = "view_tasks"
    ADD_TASKS = "add_tasks"
    UPDATE_TASKS = "update_tasks"
    UPDATE_OWN_TASK_STATUS = "update_own_task_status"
    REMOVE_TASKS = "remove_tasks"

    ASSIGN_OPEN_TASK = "assign_open_task"
    UNASSIGN_OPEN_TASK = "unassign_open_task"
