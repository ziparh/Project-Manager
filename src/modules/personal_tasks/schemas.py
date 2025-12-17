from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from common.schemas import BaseSortingParams
from enums.task import TaskPriority, TaskStatus


class PersonalTaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    deadline: datetime | None
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonalTaskCreate(BaseModel):
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


class PersonalTaskPatch(BaseModel):
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


class PersonalTaskFilterParams(BaseModel):
    """Query parameters for personal task filtering"""

    status: TaskStatus | None = Field(None, description="Filter by status")
    priority: TaskPriority | None = Field(None, description="Filter by priority")
    overdue: bool | None = Field(None, description="Filter by overdue")
    search: str | None = Field(
        None, min_length=1, description="Search by title or description"
    )


class PersonalTaskSortingParams(BaseSortingParams):
    """Query parameters for personal task sorting"""

    sort_by: Literal["deadline", "status", "priority", "created_at", "updated_at"] = (
        Field("created_at", description="Fields to sort by")
    )
