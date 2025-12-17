from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.v1.deps.services import get_auth_service
from modules.auth import service as auth_svc, schemas as auth_schemas
from modules.users import schemas as users_schemas

router = APIRouter()


@router.post("/register", response_model=users_schemas.UserRead)
async def register_user(
    register_data: auth_schemas.UserRegister,
    auth_service: auth_svc.AuthService = Depends(get_auth_service),
):
    return await auth_service.register(register_data=register_data)


@router.post("/login", response_model=auth_schemas.TokenResponse)
async def login_user(
    login_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: auth_svc.AuthService = Depends(get_auth_service),
):
    return await auth_service.login(login_data=login_data)


@router.post("/refresh", response_model=auth_schemas.TokenResponse)
async def refresh(
    refresh_request: auth_schemas.RefreshTokenRequest,
    auth_service: auth_svc.AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_tokens(refresh_token_request=refresh_request)
