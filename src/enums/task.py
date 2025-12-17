from enum import Enum


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @property
    def sort_order(self) -> int:
        match self:
            case TaskStatus.CANCELLED:
                return 4
            case TaskStatus.DONE:
                return 3
            case TaskStatus.IN_PROGRESS:
                return 2
            case TaskStatus.TODO:
                return 1


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def sort_order(self) -> int:
        match self:
            case TaskPriority.CRITICAL:
                return 4
            case TaskPriority.HIGH:
                return 3
            case TaskPriority.MEDIUM:
                return 2
            case TaskPriority.LOW:
                return 1
