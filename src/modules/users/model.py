from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import TimestampMixin

if TYPE_CHECKING:
    from modules.personal_tasks.model import PersonalTask
    from modules.projects.model import Project
    from modules.project_members.model import ProjectMember
    from modules.project_tasks.model import ProjectTask


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]

    personal_tasks: Mapped[list["PersonalTask"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise_on_sql"
    )
    created_projects: Mapped[list["Project"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan", lazy="raise_on_sql"
    )
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="raise_on_sql"
    )
    assigned_project_tasks: Mapped[list["ProjectTask"]] = relationship(
        foreign_keys="ProjectTask.assignee_id",
        back_populates="assignee",
        lazy="raise_on_sql",
    )
    created_project_tasks: Mapped[list["ProjectTask"]] = relationship(
        foreign_keys="ProjectTask.created_by_id",
        back_populates="creator",
        lazy="raise_on_sql",
    )
