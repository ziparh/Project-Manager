from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import model


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: model.User) -> model.User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_user_by_username(self, username: str) -> model.User | None:
        query = select(model.User).where(model.User.username == username)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> model.User | None:
        return await self.db.get(model.User, user_id)
