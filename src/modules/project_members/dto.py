from dataclasses import dataclass

from enums.project import ProjectRole


@dataclass
class ProjectMemberFilterDto:
    role: ProjectRole | None = None
