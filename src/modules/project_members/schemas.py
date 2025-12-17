from datetime import datetime
from pydantic import BaseModel, ConfigDict

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
