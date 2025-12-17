from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from pydantic import EmailStr

from .model import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> User:
        user = User(**data)

        self.db.add(user)
        await self.db.commit()

        return user

    async def update_by_id(self, user_id: int, update_data: dict) -> User:
        query = (
            update(User).where(User.id == user_id).values(**update_data).returning(User)
        )
        result = await self.db.execute(query)
        await self.db.commit()

        return result.scalar_one()

    async def delete_by_id(
        self,
        user_id: int,
    ):
        query = delete(User).where(User.id == user_id)

        await self.db.execute(query)
        await self.db.commit()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_username_or_email(
        self, username: str, email: EmailStr
    ) -> User | None:
        query = select(User).where(
            or_(
                User.username == username,
                User.email == email,
            )
        )
        result = await self.db.execute(query)

        return result.scalar_one_or_none()
