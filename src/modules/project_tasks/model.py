from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import TimestampMixin
from enums.task import TaskStatus, TaskPriority
from enums.project_task import ProjectTaskType

if TYPE_CHECKING:
    from modules.users.model import User
    from modules.projects.model import Project


class ProjectTask(Base, TimestampMixin):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[ProjectTaskType] = mapped_column(
        SQLEnum(ProjectTaskType), default=ProjectTaskType.DEFAULT, index=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str]
    description: Mapped[str | None]
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus), default=TaskStatus.TODO, index=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    project: Mapped["Project"] = relationship(
        back_populates="tasks", lazy="raise_on_sql"
    )
    assignee: Mapped["User | None"] = relationship(
        foreign_keys=[assignee_id],
        back_populates="assigned_project_tasks",
        lazy="raise_on_sql",
    )
    creator: Mapped["User"] = relationship(
        foreign_keys=[created_by_id],
        back_populates="created_project_tasks",
        lazy="raise_on_sql",
    )

    __table_args__ = (
        CheckConstraint(
            "type != 'DEFAULT' OR (assignee_id IS NOT NULL AND assigned_at IS NOT NULL)",
            name="ck_project_task_default_requires_assignee",
        ),
        Index("ix_project_tasks_project_type", "project_id", "type"),
        Index("ix_project_tasks_project_deadline", "project_id", "deadline"),
        Index("ix_project_tasks_project_status", "project_id", "status"),
        Index("ix_project_tasks_project_priority", "project_id", "priority"),
    )
