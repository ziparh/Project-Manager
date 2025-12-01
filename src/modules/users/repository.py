from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from pydantic import EmailStr

from . import model


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: model.User) -> model.User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        await self.db.commit()

        return user

    async def update_by_id(self, user_id: int, update_data: dict) -> model.User:
        query = (
            update(model.User)
            .where(model.User.id == user_id)
            .values(**update_data)
            .returning(model.User)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        await self.db.commit()

        return result.scalar_one()

    async def delete_by_id(
        self,
        user_id: int,
    ):
        query = delete(model.User).where(model.User.id == user_id)

        await self.db.execute(query)
        await self.db.commit()

    async def get_by_id(self, user_id: int) -> model.User | None:
        return await self.db.get(model.User, user_id)

    async def get_by_username(self, username: str) -> model.User | None:
        query = select(model.User).where(model.User.username == username)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> model.User | None:
        query = select(model.User).where(model.User.email == email)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_by_username_or_email(
        self, username: str, email: EmailStr
    ) -> model.User | None:
        query = select(model.User).where(
            or_(
                model.User.username == username,
                model.User.email == email,
            )
        )
        result = await self.db.execute(query)

        return result.scalar_one_or_none()
