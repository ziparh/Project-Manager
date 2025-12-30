from typing import Sequence
from sqlalchemy import select, func, Select, asc, desc, and_, or_, case
from sqlalchemy.orm import selectinload, aliased
from sqlalchemy.ext.asyncio import AsyncSession

from . import model, dto
from common.dto import PaginationDto, SortingDto
from modules.users.model import User as UserModel
from enums.task import TaskStatus, TaskPriority
from utils.datetime import utc_now


class ProjectTaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, project_id: int, created_by_id: int, data: dict
    ) -> model.ProjectTask:
        task = model.ProjectTask(
            project_id=project_id,
            created_by_id=created_by_id,
            **data,
        )

        self.db.add(task)
        await self.db.commit()

        full_task = await self.get_by_id(task.id)

        return full_task

    async def get_all(
        self,
        project_id: int,
        filters: dto.ProjectTaskFilterDto,
        sorting: SortingDto,
        pagination: PaginationDto,
    ) -> tuple[Sequence[model.ProjectTask], int]:
        # Basic stmt
        stmt = (
            select(model.ProjectTask)
            .where(model.ProjectTask.project_id == project_id)
            .options(
                selectinload(model.ProjectTask.project),
                selectinload(model.ProjectTask.assignee),
                selectinload(model.ProjectTask.creator),
            )
        )

        # Apply filters
        stmt = self._apply_filters(stmt, filters)

        # Calculate the total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply sorting
        stmt = self._apply_sorting(stmt, sorting)

        # Apply pagination
        stmt = stmt.limit(pagination.size).offset(pagination.offset)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total

    async def get_by_id(self, task_id: int) -> model.ProjectTask:
        stmt = (
            select(model.ProjectTask)
            .where(model.ProjectTask.id == task_id)
            .options(
                selectinload(model.ProjectTask.project),
                selectinload(model.ProjectTask.assignee),
                selectinload(model.ProjectTask.creator),
            )
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def update_by_task(
        self, task: model.ProjectTask, data: dict
    ) -> model.ProjectTask:
        for key, value in data.items():
            setattr(task, key, value)

        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def delete_by_task(self, task: model.ProjectTask) -> None:
        await self.db.delete(task)
        await self.db.commit()

    def _apply_filters(self, stmt: Select, filters: dto.ProjectTaskFilterDto) -> Select:
        if filters.type:
            stmt = stmt.where(model.ProjectTask.type == filters.type)

        if filters.assignee_id:
            stmt = stmt.where(model.ProjectTask.assignee_id == filters.assignee_id)

        if filters.created_by_id:
            stmt = stmt.where(model.ProjectTask.created_by_id == filters.created_by_id)

        if filters.status:
            stmt = stmt.where(model.ProjectTask.status == filters.status)

        if filters.priority:
            stmt = stmt.where(model.ProjectTask.priority == filters.priority)

        if filters.overdue is not None:
            now = utc_now()
            if filters.overdue:
                # Overdue = deadline passed AND status not completed/canceled
                stmt = stmt.where(
                    and_(
                        model.ProjectTask.deadline < now,
                        model.ProjectTask.status.notin_(
                            [TaskStatus.DONE, TaskStatus.CANCELLED]
                        ),
                    )
                )
            else:
                # Not Overdue = deadline in the future OR no deadline OR status completed/canceled
                stmt = stmt.where(
                    or_(
                        model.ProjectTask.deadline >= now,
                        model.ProjectTask.deadline.is_(None),
                        model.ProjectTask.status.in_(
                            [TaskStatus.DONE, TaskStatus.CANCELLED]
                        ),
                    )
                )

        if filters.search:
            assignee_alias = aliased(UserModel)
            creator_alias = aliased(UserModel)

            stmt = stmt.outerjoin(assignee_alias, model.ProjectTask.assignee)
            stmt = stmt.outerjoin(creator_alias, model.ProjectTask.creator)

            search_term = f"%{filters.search}%"
            search_filters = [
                model.ProjectTask.title.ilike(search_term),
                model.ProjectTask.description.ilike(search_term),
                assignee_alias.username.ilike(search_term),
                creator_alias.username.ilike(search_term),
            ]

            stmt = stmt.where(or_(*search_filters))

        return stmt

    def _apply_sorting(self, stmt: Select, sorting: SortingDto):
        # Sort by
        if sorting.sort_by == "priority":
            sort_by = self._get_priority_order_case()
        elif sorting.sort_by == "status":
            sort_by = self._get_status_order_case()
        else:
            sort_by = getattr(model.ProjectTask, sorting.sort_by)

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
            (model.ProjectTask.priority == priority.name, priority.sort_order)
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
            (model.ProjectTask.status == status.name, status.sort_order)
            for status in TaskStatus
        ]

        return case(*order, else_=0)
