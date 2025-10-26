from fastapi import HTTPException, status

from core.security.password import PasswordHasher
from . import repository, schemas


class UserService:
    def __init__(self, repo: repository.UserRepository):
        self.repo = repo

    async def list_users(self):
        return await self.repo.get_all()

    async def register_user(self, user_data: schemas.UserCreate):
        if await self.repo.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            )
        hashed_password = PasswordHasher.hash(user_data.password)
        user_data.password = hashed_password

        user = await self.repo.create(user_data)
        await self.repo.db.commit()

        return user
