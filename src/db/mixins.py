from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("(NOW() AT TIME ZONE 'UTC')"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("(NOW() AT TIME ZONE 'UTC')"),
        onupdate=text("(NOW() AT TIME ZONE 'UTC')"),
        nullable=False,
    )