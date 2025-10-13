from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import schemas, model


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: schemas.UserCreate):
        db_user = model.User(
            username=user.username,
            hashed_password=user.password,
        )
        self.db.add(db_user)

        await self.db.flush()
        await self.db.refresh(db_user)

        return db_user

    async def get_by_username(self, username: str):
        query = select(model.User).where(model.User.username == username)
        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_all(self):
        query = select(model.User)
        result = await self.db.execute(query)

        return result.scalars().all()
