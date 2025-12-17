from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from common.schemas import BaseSortingParams
from enums.project import ProjectStatus, ProjectRole


class ProjectCreatorRead(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberBrief(BaseModel):
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectRead(BaseModel):
    id: int
    title: str
    description: str | None
    deadline: datetime | None
    status: ProjectStatus
    creator: ProjectCreatorRead
    members: list[ProjectMemberBrief]

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(min_length=1, max_length=1000)] = None
    deadline: datetime | None = None
    status: ProjectStatus = ProjectStatus.PLANNING

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_string(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class ProjectPatch(BaseModel):
    title: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    description: Annotated[str | None, Field(min_length=1, max_length=1000)] = None
    deadline: datetime | None = None
    status: ProjectStatus | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_string(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class ProjectFilterParams(BaseModel):
    """Query parameters for project filtering"""

    creator_id: int | None = Field(None, description="Filter by creator id")
    status: ProjectStatus | None = Field(None, description="Filter by status")
    role: ProjectRole | None = Field(None, description="Filter by role in project")
    overdue: bool | None = Field(None, description="Filter by overdue")
    search: str | None = Field(
        None, description="Search by title, description or creator name"
    )


class ProjectSortingParams(BaseSortingParams):
    """Query parameters for project sorting"""

    sort_by: Literal["deadline", "status", "created_at", "updated_at"] = Field(
        "created_at", description="Fields to sort by"
    )
