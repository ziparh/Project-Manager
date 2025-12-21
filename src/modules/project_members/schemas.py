from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from common.schemas import BaseSortingParams
from enums.project import ProjectRole


class UserBrief(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberRead(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime

    user: UserBrief

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: ProjectRole


class ProjectMemberPatch(BaseModel):
    role: ProjectRole


class ProjectMemberFilterParams(BaseModel):
    role: ProjectRole | None = Field(None, description="Filter by role")


class ProjectMemberSortingParams(BaseSortingParams):
    sort_by: Literal["role", "joined_at"] = Field("joined_at", description="Fields to sort by")
