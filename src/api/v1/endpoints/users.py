from fastapi import APIRouter, Depends, Response, status

from api.deps import get_user_service, get_authenticate_user
from modules.users import schemas, service, model

router = APIRouter()


@router.get("/me", response_model=schemas.UserRead)
async def get_users_me(user: model.User = Depends(get_authenticate_user)):
    return user


@router.patch("/me", response_model=schemas.UserRead)
async def patch_users_me(
    update_data: schemas.UserPatch,
    user: model.User = Depends(get_authenticate_user),
    user_service: service.UserService = Depends(get_user_service),
):
    return await user_service.update_me(update_data=update_data, user=user)


@router.delete("/me")
async def delete_users_me(
    user: model.User = Depends(get_authenticate_user),
    user_service: service.UserService = Depends(get_user_service),
):
    await user_service.delete_me(user=user)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
