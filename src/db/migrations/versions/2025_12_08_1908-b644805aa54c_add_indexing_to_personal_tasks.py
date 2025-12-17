"""add indexing to personal tasks

Revision ID: b644805aa54c
Revises: 1930d8fb1801
Create Date: 2025-12-08 19:08:16.018555

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b644805aa54c"
down_revision: Union[str, Sequence[str], None] = "1930d8fb1801"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_personal_tasks_user_created_at",
        "personal_tasks",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_personal_tasks_user_deadline",
        "personal_tasks",
        ["user_id", "deadline"],
        unique=False,
    )
    op.create_index(
        "ix_personal_tasks_user_priority",
        "personal_tasks",
        ["user_id", "priority"],
        unique=False,
    )
    op.create_index(
        "ix_personal_tasks_user_status",
        "personal_tasks",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_personal_tasks_user_updated_at",
        "personal_tasks",
        ["user_id", "updated_at"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_personal_tasks_user_updated_at", table_name="personal_tasks")
    op.drop_index("ix_personal_tasks_user_status", table_name="personal_tasks")
    op.drop_index("ix_personal_tasks_user_priority", table_name="personal_tasks")
    op.drop_index("ix_personal_tasks_user_deadline", table_name="personal_tasks")
    op.drop_index("ix_personal_tasks_user_created_at", table_name="personal_tasks")
    # ### end Alembic commands ###
