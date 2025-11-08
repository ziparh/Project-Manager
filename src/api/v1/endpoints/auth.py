from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.deps import get_auth_service
from modules.auth import service, schemas

router = APIRouter()


@router.post("/register", response_model=schemas.UserRead)
async def register(
    register_data: schemas.UserRegister,
    auth_service: service.AuthService = Depends(get_auth_service),
):
    return await auth_service.register_user(register_data=register_data)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    login_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: service.AuthService = Depends(get_auth_service),
):
    return await auth_service.login_user(login_data=login_data)


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    refresh_token: str,
    auth_service: service.AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_access_token(refresh_token=refresh_token)
