from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import model, schemas


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: schemas.UserCreate) -> model.User:
        db_user = model.User(
            username=user_data.username,
            hashed_password=user_data.password,
        )
        self.db.add(db_user)

        await self.db.commit()

        await self.db.flush()
        await self.db.refresh(db_user)

        return db_user

    async def get_user_by_username(self, username: str) -> model.User:
        query = select(model.User).where(model.User.username == username)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> model.User:
        query = select(model.User).where(model.User.id == user_id)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_all(self) -> list[model.User]:
        query = select(model.User)
        result = await self.db.execute(query)

        return result.scalars().all()
