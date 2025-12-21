from typing import Sequence
from datetime import datetime
from sqlalchemy import select, Select, ColumnElement, case, asc, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import model, dto as member_dto
from common import dto as common_dto
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

    async def get_all(
        self,
        project_id: int,
        filters: member_dto.ProjectMemberFilterDto,
        sorting: common_dto.SortingDto,
        pagination: common_dto.PaginationDto,
    ) -> tuple[Sequence[model.ProjectMember], int]:
        # Basic stmt
        stmt = (
            select(model.ProjectMember)
            .where(model.ProjectMember.project_id == project_id)
            .options(selectinload(model.ProjectMember.user))
        )

        # Apply filters
        stmt = self._apply_filters(stmt, filters)

        # Calculate the total count
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_query) or 0

        # Apply sorting
        stmt = self._apply_sorting(stmt, sorting)

        # Apply pagination
        stmt = stmt.limit(pagination.size).offset(pagination.offset)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total

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

    def _apply_filters(
        self, stmt: Select, filters: member_dto.ProjectMemberFilterDto
    ) -> Select:
        if filters.role:
            stmt = stmt.where(model.ProjectMember.role == filters.role)

        return stmt

    def _apply_sorting(self, stmt: Select, sorting: common_dto.SortingDto) -> Select:
        # Sort by
        if sorting.sort_by == "role":
            sort_by = self._get_role_order_case()
        else:
            sort_by = getattr(model.ProjectMember, sorting.sort_by)

        # Order by
        if sorting.order == "asc":
            stmt = stmt.order_by(asc(sort_by))
        else:
            stmt = stmt.order_by(desc(sort_by))

        return stmt

    def _get_role_order_case(self) -> ColumnElement[int]:
        """
        Returns sql case for sorting by priority
        - OWNER = 3
        - ADMIN = 2
        - MEMBER = 1
        """
        order = [
            (model.ProjectMember.role == role.name, role.sort_order)
            for role in ProjectRole
        ]

        return case(*order, else_=0)
