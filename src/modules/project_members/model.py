from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import JoinedAtMixin
from enums.project import ProjectRole

if TYPE_CHECKING:
    from modules.users.model import User
    from modules.projects.model import Project


class ProjectMember(Base, JoinedAtMixin):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[ProjectRole] = mapped_column(
        SQLEnum(ProjectRole), default=ProjectRole.MEMBER, index=True
    )

    project: Mapped["Project"] = relationship(
        back_populates="members", lazy="raise_on_sql"
    )
    user: Mapped["User"] = relationship(
        back_populates="project_memberships", lazy="raise_on_sql"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
        Index("ix_project_user", "project_id", "user_id"),
    )
