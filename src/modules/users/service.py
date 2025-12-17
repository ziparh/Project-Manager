from fastapi import HTTPException, status

from . import (
    repository as user_repository,
    model as user_model,
    schemas as user_schemas,
)
from core.security.password import PasswordHasher


class UserService:
    def __init__(
        self,
        user_repo: user_repository.UserRepository,
    ):
        self.user_repo = user_repo

    async def update_me(
        self, update_data: user_schemas.UserPatch, user: user_model.User
    ) -> user_model.User:
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
            )

        if "username" in update_dict:
            if await self.user_repo.get_by_username(update_dict["username"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username already taken",
                )

        if "email" in update_dict:
            if await self.user_repo.get_by_email(update_dict["email"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

        if "password" in update_dict:
            update_dict["hashed_password"] = PasswordHasher.hash(
                update_dict["password"]
            )
            update_dict.pop("password")

        updated_user = await self.user_repo.update_by_id(
            user_id=user.id,
            update_data=update_dict,
        )

        return updated_user

    async def delete_me(self, user: user_model.User):
        await self.user_repo.delete_by_id(user_id=user.id)
