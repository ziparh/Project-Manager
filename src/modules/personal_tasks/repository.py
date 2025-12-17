from sqlalchemy import select, update, delete, or_, and_, func, asc, desc, Select, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from datetime import datetime, timezone

from . import model, dto as tasks_dto
from common import dto as common_dto
from enums.task import TaskStatus, TaskPriority


class PersonalTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        user_id: int,
        filters: tasks_dto.PersonalTaskFilterDto,
        sorting: common_dto.SortingDto,
        pagination: common_dto.PaginationDto,
    ) -> tuple[Sequence[model.PersonalTask], int]:
        # Basic query
        stmt = select(model.PersonalTask).where(model.PersonalTask.user_id == user_id)

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

    async def get_by_id_and_user(
        self, task_id: int, user_id: int
    ) -> model.PersonalTask | None:
        stmt = (
            select(model.PersonalTask)
            .where(model.PersonalTask.id == task_id)
            .where(model.PersonalTask.user_id == user_id)
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create(self, user_id: int, data: dict) -> model.PersonalTask:
        obj = model.PersonalTask(
            user_id=user_id,
            **data,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)

        return obj

    async def update_by_id(self, task_id: int, data: dict) -> model.PersonalTask:
        stmt = (
            update(model.PersonalTask)
            .where(model.PersonalTask.id == task_id)
            .values(**data)
            .returning(model.PersonalTask)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.scalar_one()

    async def delete_by_id(self, task_id: int) -> None:
        stmt = delete(model.PersonalTask).where(model.PersonalTask.id == task_id)

        await self.db.execute(stmt)
        await self.db.commit()

    def _apply_filters(
        self, query: Select, filters: tasks_dto.PersonalTaskFilterDto
    ) -> Select:
        if filters.status:
            query = query.where(model.PersonalTask.status == filters.status)

        if filters.priority:
            query = query.where(model.PersonalTask.priority == filters.priority)

        if filters.overdue is not None:
            now = datetime.now(timezone.utc)
            if filters.overdue:
                # Overdue = deadline passed AND status not completed/canceled
                query = query.where(
                    and_(
                        model.PersonalTask.deadline < now,
                        model.PersonalTask.status.notin_(
                            [TaskStatus.DONE, TaskStatus.CANCELLED]
                        ),
                    )
                )
            else:
                # Not Overdue = deadline in the future OR no deadline OR status completed/canceled
                query = query.where(
                    or_(
                        model.PersonalTask.deadline >= now,
                        model.PersonalTask.deadline.is_(None),
                        model.PersonalTask.status.in_(
                            [TaskStatus.DONE, TaskStatus.CANCELLED]
                        ),
                    )
                )

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    model.PersonalTask.title.ilike(search_term),
                    model.PersonalTask.description.ilike(search_term),
                )
            )

        return query

    def _apply_sorting(self, stmt: Select, sorting: common_dto.SortingDto):
        # Sort by
        if sorting.sort_by == "priority":
            sort_by = self._get_priority_order_case()
        elif sorting.sort_by == "status":
            sort_by = self._get_status_order_case()
        else:
            sort_by = getattr(model.PersonalTask, sorting.sort_by)

        # Sort order
        if sorting.order == "asc":
            stmt = stmt.order_by(asc(sort_by))
        else:
            stmt = stmt.order_by(desc(sort_by))

        return stmt

    def _get_priority_order_case(self):
        """
        Returns sql case for sorting by priority
        - CRITICAL = 4
        - HIGH = 3
        - MEDIUM = 2
        - LOW = 1
        """
        order = [
            (model.PersonalTask.priority == priority.name, priority.sort_order)
            for priority in TaskPriority
        ]

        return case(*order, else_=0)

    def _get_status_order_case(self):
        """
        Returns sql case for sorting by priority
        - CANCELLED = 4
        - DONE = 3
        - IN_PROGRESS = 2
        - TODO = 1
        """
        order = [
            (model.PersonalTask.status == status.name, status.sort_order)
            for status in TaskStatus
        ]

        return case(*order, else_=0)
