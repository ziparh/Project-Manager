from dataclasses import dataclass
from enums.task import TaskPriority, TaskStatus


@dataclass
class PersonalTaskFilterDto:
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    overdue: bool | None = None
    search: str | None = None