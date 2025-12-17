"""Create project members table

Revision ID: ed44de2a2699
Revises: febc1654a486
Create Date: 2025-12-08 19:44:39.971849

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ed44de2a2699"
down_revision: Union[str, Sequence[str], None] = "febc1654a486"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("OWNER", "ADMIN", "MEMBER", name="projectrole"),
            nullable=False,
        ),
        sa.Column("joined_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )
    op.create_index(
        op.f("ix_project_members_project_id"),
        "project_members",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_members_user_id"),
        "project_members",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_user",
        "project_members",
        ["project_id", "user_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_project_user", table_name="project_members")
    op.drop_index(op.f("ix_project_members_user_id"), table_name="project_members")
    op.drop_index(op.f("ix_project_members_project_id"), table_name="project_members")
    op.drop_table("project_members")
    # ### end Alembic commands ###
