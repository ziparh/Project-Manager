from dataclasses import dataclass
from enums.task import TaskStatus, TaskPriority
from enums.project_task import ProjectTaskType


@dataclass
class ProjectTaskFilterDto:
    type: ProjectTaskType | None = None
    assignee_id: int | None = None
    created_by_id: int | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    overdue: bool | None = None
    search: str | None = None
