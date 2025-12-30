from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from common.schemas import BaseSortingParams
from enums.project_task import ProjectTaskType
from enums.task import TaskStatus, TaskPriority


class ProjectBrief(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBrief(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ProjectTaskRead(BaseModel):
    id: int
    type: ProjectTaskType
    title: str
    description: str | None
    deadline: datetime | None
    priority: TaskPriority
    status: TaskStatus
    assigned_at: datetime | None
    created_at: datetime
    updated_at: datetime

    project: ProjectBrief
    assignee: UserBrief | None
    creator: UserBrief

    model_config = ConfigDict(from_attributes=True)


class ProjectTaskCreate(BaseModel):
    type: ProjectTaskType
    assignee_id: int | None = None
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(min_length=1, max_length=1000)] = None
    deadline: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_string(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @model_validator(mode="after")
    def check_assignee(self):
        if self.type == ProjectTaskType.DEFAULT and self.assignee_id is None:
            raise ValueError("assignee_id must be set when type is DEFAULT")
        if self.type == ProjectTaskType.OPEN and self.assignee_id is not None:
            raise ValueError("assignee_id must be None when type is OPEN")

        return self


class ProjectTaskPatch(BaseModel):
    assignee_id: int | None = None
    title: Annotated[str | None, Field(min_length=1, max_length=200)] = None
    description: Annotated[str | None, Field(min_length=1, max_length=1000)] = None
    deadline: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_string(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class ProjectTasksFiltersParams(BaseModel):
    """Query parameters for project tasks filtering"""

    type: ProjectTaskType | None = Field(None, description="Filter by type")
    assignee_id: int | None = Field(None, description="Filter by assignee_id")
    created_by_id: int | None = Field(None, description="Filter by created_by_id")
    status: TaskStatus | None = Field(None, description="Filter by status")
    priority: TaskPriority | None = Field(None, description="Filter by priority")
    overdue: bool | None = Field(None, description="Filter by overdue")
    search: str | None = Field(
        None,
        min_length=1,
        description="Search by title, description, assignee name or creator name",
    )


class ProjectTasksSortingParams(BaseSortingParams):
    """Query parameters for project tasks sorting"""

    sort_by: Literal[
        "deadline", "status", "priority", "assigned_at", "created_at", "updated_at"
    ] = Field("created_at", description="Fields to sort by")
