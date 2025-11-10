from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class UserRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=15)]
    password: Annotated[str, Field(..., min_length=6)]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
