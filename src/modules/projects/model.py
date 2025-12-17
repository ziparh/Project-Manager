from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import TimestampMixin
from enums.project import ProjectStatus

if TYPE_CHECKING:
    from modules.users.model import User
    from modules.project_members.model import ProjectMember


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str]
    description: Mapped[str | None]
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus), default=ProjectStatus.PLANNING
    )

    creator: Mapped["User"] = relationship(
        back_populates="created_projects", lazy="raise_on_sql"
    )
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="raise_on_sql"
    )
