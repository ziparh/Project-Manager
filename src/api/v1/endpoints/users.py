from fastapi import APIRouter, Depends

from api.deps import get_user_service
from modules.users import schemas, service

router = APIRouter()


@router.get("/all/", response_model=list[schemas.UserRead])
async def get_users(user_service: service.UserService = Depends(get_user_service)):
    return await user_service.list_users()


@router.post("/register/")
async def register(
    user_data: schemas.UserCreate,
    user_service: service.UserService = Depends(get_user_service),
):
    return await user_service.register_user(user_data)
