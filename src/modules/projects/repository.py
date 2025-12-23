from typing import Sequence
from datetime import datetime, timezone
from sqlalchemy import (
    select,
    update,
    delete,
    func,
    Select,
    asc,
    desc,
    case,
    ColumnElement,
    or_,
    and_,
)
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import model as project_model, dto as project_dto
from modules.project_members import model as member_model
from modules.users import model as user_model
from common import dto as common_dto
from enums.project import ProjectRole, ProjectStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, data: dict) -> project_model.Project:
        project = project_model.Project(
            creator_id=user_id,
            **data,
        )

        project.members.append(
            member_model.ProjectMember(
                user_id=user_id,
                role=ProjectRole.OWNER,
            )
        )

        self.db.add(project)
        await self.db.commit()

        full_project = await self.get_by_id(project.id)

        return full_project

    async def get_all(
        self,
        user_id: int,
        filters: project_dto.ProjectFilterDto,
        sorting: common_dto.SortingDto,
        pagination: common_dto.PaginationDto,
    ) -> tuple[Sequence[project_model.Project], int]:
        # Basic stmt
        stmt = (
            select(project_model.Project)
            .join(project_model.Project.members)
            .where(member_model.ProjectMember.user_id == user_id)
            .options(
                selectinload(project_model.Project.creator),
                selectinload(project_model.Project.members),
            )
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

    async def get_by_id(self, project_id: int) -> project_model.Project | None:
        stmt = (
            select(project_model.Project)
            .where(project_model.Project.id == project_id)
            .options(
                selectinload(project_model.Project.creator),
                selectinload(project_model.Project.members),
            )
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def update_by_id(
        self, project_id: int, data: dict
    ) -> project_model.Project | None:
        stmt = (
            update(project_model.Project)
            .where(project_model.Project.id == project_id)
            .values(**data)
            .returning(project_model.Project.id)
        )

        result = await self.db.execute(stmt)
        project_id = result.scalar_one_or_none()

        if project_id is None:
            return None
        await self.db.commit()

        full_project = await self.get_by_id(project_id)

        return full_project


    async def delete_by_id(self, project_id: int) -> None:
        stmt = delete(project_model.Project).where(
            project_model.Project.id == project_id
        )

        await self.db.execute(stmt)
        await self.db.commit()

    def _apply_filters(
        self, stmt: Select, filters: project_dto.ProjectFilterDto
    ) -> Select:
        if filters.creator_id:
            stmt = stmt.where(project_model.Project.creator_id == filters.creator_id)

        if filters.status:
            stmt = stmt.where(project_model.Project.status == filters.status)

        if filters.role:
            stmt = stmt.where(member_model.ProjectMember.role == filters.role)

        if filters.overdue is not None:
            now = datetime.now(timezone.utc)
            if filters.overdue:
                # Overdue = deadline passed AND status not completed/canceled
                stmt = stmt.where(
                    and_(
                        project_model.Project.deadline < now,
                        project_model.Project.status.notin_(
                            [ProjectStatus.CANCELLED, ProjectStatus.COMPLETED]
                        ),
                    )
                )
            else:
                # Not Overdue = deadline in the future OR no deadline OR status completed/canceled
                stmt = stmt.where(
                    or_(
                        project_model.Project.deadline >= now,
                        project_model.Project.deadline.is_(None),
                        project_model.Project.status.in_(
                            [ProjectStatus.CANCELLED, ProjectStatus.COMPLETED]
                        ),
                    )
                )

        if filters.search:
            stmt = stmt.join(project_model.Project.creator)

            search_term = f"%{filters.search}%"
            search_filters = [
                project_model.Project.title.ilike(search_term),
                project_model.Project.description.ilike(search_term),
                user_model.User.username.ilike(search_term),
            ]

            stmt = stmt.where(or_(*search_filters))

        return stmt

    def _apply_sorting(self, stmt: Select, sorting: common_dto.SortingDto) -> Select:
        # Sort by
        if sorting.sort_by == "status":
            sort_by = self._get_status_order_case()
        else:
            sort_by = getattr(project_model.Project, sorting.sort_by)

        # Order by
        if sorting.order == "asc":
            stmt = stmt.order_by(asc(sort_by))
        else:
            stmt = stmt.order_by(desc(sort_by))

        return stmt

    def _get_status_order_case(self) -> ColumnElement[int]:
        """
        Returns sql case for sorting by priority
        - CANCELLED = 5
        - COMPLETED = 4
        - ACTIVE = 3
        - ON_HOLD = 2
        - PLANNING = 1
        """
        order = [
            (project_model.Project.status == status.name, status.sort_order)
            for status in ProjectStatus
        ]

        return case(*order, else_=0)
