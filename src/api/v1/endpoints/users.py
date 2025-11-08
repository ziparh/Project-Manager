from fastapi import APIRouter, Depends

from api.deps import get_user_service, oauth2_scheme
from modules.users import schemas, service

router = APIRouter()


@router.get("/me", response_model=schemas.UserRead)
async def get_me(
    token: str = Depends(oauth2_scheme),
    user_service: service.UserService = Depends(get_user_service),
):
    return await user_service.get_users_me(token=token)
