from sqlalchemy import select, update, delete, or_, and_, func, asc, desc, Select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from . import model, dto as tasks_dto
from common import dto as common_dto
from enums.task import TaskStatus


class PersonalTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def get_list(
        self,
        user_id: int,
        filters: tasks_dto.PersonalTaskFilterDto,
        sorting: common_dto.SortingDto,
        pagination: common_dto.PaginationDto,
    ):
        # Basic query
        stmt = select(model.PersonalTask).where(model.PersonalTask.user_id == user_id)

        # Apply filters
        stmt = self._apply_filters(stmt, filters)

        # Calculate the total count
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_query) or 0

        # Apply sorting
        sort_field = getattr(model.PersonalTask, sorting.sort_by)
        if sorting.order == "asc":
            stmt = stmt.order_by(asc(sort_field))
        else:
            stmt = stmt.order_by(desc(sort_field))

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
