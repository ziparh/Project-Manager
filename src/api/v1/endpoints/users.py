from fastapi import APIRouter, Depends, Response, status

from api.deps import get_user_service, oauth2_scheme
from modules.users import schemas, service

router = APIRouter()


@router.get("/me", response_model=schemas.UserRead)
async def get_users_me(
    token: str = Depends(oauth2_scheme),
    user_service: service.UserService = Depends(get_user_service),
):
    return await user_service.get_me(token=token)


@router.patch("/me", response_model=schemas.UserRead)
async def patch_users_me(
    update_data: schemas.UserPatch,
    token: str = Depends(oauth2_scheme),
    user_service: service.UserService = Depends(get_user_service),
):
    return await user_service.update_me(
        update_data=update_data,
        token=token,
    )


@router.delete("/me")
async def delete_users_me(
    token: str = Depends(oauth2_scheme),
    user_service: service.UserService = Depends(get_user_service),
):
    await user_service.delete_me(token=token)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
