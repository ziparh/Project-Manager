from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import TimestampMixin
from enums.task import TaskStatus, TaskPriority

if TYPE_CHECKING:
    from modules.users.model import User


class PersonalTask(Base, TimestampMixin):
    __tablename__ = "personal_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str]
    description: Mapped[str | None]
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority),
        default=TaskPriority.MEDIUM,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus), default=TaskStatus.TODO
    )

    user: Mapped["User"] = relationship(
        back_populates="personal_tasks", lazy="raise_on_sql"
    )

    __table_args__ = (
        Index("ix_personal_tasks_user_deadline", "user_id", "deadline"),
        Index("ix_personal_tasks_user_priority", "user_id", "priority"),
        Index("ix_personal_tasks_user_status", "user_id", "status"),
    )
