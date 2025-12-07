from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator

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
    title: Annotated[
        str, BeforeValidator(str.strip), Field(min_length=1, max_length=200)
    ]
    description: Annotated[
        str | None, BeforeValidator(str.strip), Field(max_length=1000)
    ] = None
    deadline: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO


class PersonalTaskPatch(BaseModel):
    title: Annotated[
        str | None, BeforeValidator(str.strip), Field(min_length=1, max_length=200)
    ] = None
    description: Annotated[
        str | None, BeforeValidator(str.strip), Field(max_length=1000)
    ] = None
    deadline: datetime | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None


class PersonalTaskFilterParams(BaseModel):
    """Query parameters for task filtering"""

    status: TaskStatus | None = Field(None, description="Filter by status")
    priority: TaskPriority | None = Field(None, description="Filter by priority")
    overdue: bool | None = Field(None, description="Filter by overdue")
    search: str | None = Field(
        None, min_length=1, description="Search in title/description"
    )


class PersonalTaskSortingParams(BaseSortingParams):
    """Query parameters for task sorting"""

    sort_by: Literal["deadline", "priority", "created_at", "updated_at"] = Field(
        "created_at", description="Fields to sort by"
    )
