"""Rework CheckConstraint in project tasks

Revision ID: acfd5181a915
Revises: 0aa84622a8e9
Create Date: 2025-12-29 23:26:30.425957

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "acfd5181a915"
down_revision: Union[str, Sequence[str], None] = "0aa84622a8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "ck_project_task_default_requires_assignee",
        "project_tasks",
        type_="check",
    )

    op.create_check_constraint(
        "ck_project_task_default_requires_assignee",
        "project_tasks",
        "type != 'DEFAULT' OR (assignee_id IS NOT NULL AND assigned_at IS NOT NULL)",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_project_task_default_requires_assignee",
        "project_tasks",
        type_="check",
    )

    op.create_check_constraint(
        "ck_project_task_default_requires_assignee",
        "project_tasks",
        "type = 'DEFAULT' AND assignee_id IS NOT NULL AND assigned_at IS NOT NULL",
    )
    # ### end Alembic commands ###
