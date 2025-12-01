from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPatch(BaseModel):
    username: Annotated[str | None, Field(min_length=3, max_length=15)] = None
    email: EmailStr | None = None
    password: Annotated[str | None, Field(min_length=6)] = None
