from dataclasses import dataclass
from enums.project import ProjectStatus, ProjectRole


@dataclass
class ProjectFilterDto:
    creator_id: int | None = None
    status: ProjectStatus | None = None
    role: ProjectRole | None = None
    overdue: bool | None = None
    search: str | None = None
