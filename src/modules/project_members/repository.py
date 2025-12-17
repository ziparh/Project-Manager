from typing import Sequence
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import model
from enums.project import ProjectRole


class ProjectMemberRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, project_id: int, user_id: int, role: ProjectRole, joined_at: datetime
    ) -> model.ProjectMember:
        membership = model.ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            joined_at=joined_at,
        )

        self.db.add(membership)
        await self.db.commit()

        return membership

    async def get_all_by_project_id(
        self,
        project_id: int,
    ) -> Sequence[model.ProjectMember]:
        stmt = (
            select(model.ProjectMember)
            .where(model.ProjectMember.project_id == project_id)
            .options(selectinload(model.ProjectMember.user))
        )

        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def get_by_user_id_and_project_id(
        self, user_id: int, project_id: int
    ) -> model.ProjectMember | None:
        stmt = select(model.ProjectMember).where(
            model.ProjectMember.user_id == user_id,
            model.ProjectMember.project_id == project_id,
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def update_by_membership(
        self, membership: model.ProjectMember, data: dict
    ) -> model.ProjectMember:
        for key, value in data.items():
            setattr(membership, key, value)

        await self.db.commit()
        await self.db.refresh(membership)

        return membership

    async def delete_by_membership(self, membership: model.ProjectMember) -> None:
        await self.db.delete(membership)
        await self.db.commit()
