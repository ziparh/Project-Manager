from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from db.mixins import TimestampMixin

if TYPE_CHECKING:
    from modules.personal_tasks.model import PersonalTask


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]

    personal_tasks: Mapped[list["PersonalTask"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
