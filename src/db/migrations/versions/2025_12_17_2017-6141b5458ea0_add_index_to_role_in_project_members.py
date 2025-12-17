"""Add index to role in project_members

Revision ID: 6141b5458ea0
Revises: ed44de2a2699
Create Date: 2025-12-17 20:17:01.933503

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6141b5458ea0"
down_revision: Union[str, Sequence[str], None] = "ed44de2a2699"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        op.f("ix_project_members_role"),
        "project_members",
        ["role"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_project_members_role"), table_name="project_members")
    # ### end Alembic commands ###
