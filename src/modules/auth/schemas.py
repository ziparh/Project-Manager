from typing import Annotated

from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=15)]
    email: EmailStr
    password: Annotated[str, Field(..., min_length=6)]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
