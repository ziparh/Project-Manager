from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


class UserRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=15)]
    password: Annotated[str, Field(..., min_length=6)]


class UserLogin(BaseModel):
    username: Annotated[str, Field(...)]
    password: Annotated[str, Field(...)]
