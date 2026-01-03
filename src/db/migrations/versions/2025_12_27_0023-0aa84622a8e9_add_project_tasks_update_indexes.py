"""Add project tasks; update indexes

Revision ID: 0aa84622a8e9
Revises: 6141b5458ea0
Create Date: 2025-12-27 00:23:04.934748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0aa84622a8e9"
down_revision: Union[str, Sequence[str], None] = "6141b5458ea0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "project_tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "type",
            sa.Enum("DEFAULT", "OPEN", name="projecttasktype"),
            nullable=False,
        ),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="taskpriority",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "TODO",
                "IN_PROGRESS",
                "DONE",
                "CANCELLED",
                name="taskstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type = 'DEFAULT' AND assignee_id IS NOT NULL AND assigned_at IS NOT NULL",
            name="ck_project_task_default_requires_assignee",
        ),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_project_tasks_assignee_id"),
        "project_tasks",
        ["assignee_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_tasks_created_by_id"),
        "project_tasks",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_tasks_priority"),
        "project_tasks",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "ix_project_tasks_project_deadline",
        "project_tasks",
        ["project_id", "deadline"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_tasks_project_id"),
        "project_tasks",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_project_tasks_project_priority",
        "project_tasks",
        ["project_id", "priority"],
        unique=False,
    )
    op.create_index(
        "ix_project_tasks_project_status",
        "project_tasks",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_project_tasks_project_type",
        "project_tasks",
        ["project_id", "type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_tasks_status"),
        "project_tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_tasks_type"), "project_tasks", ["type"], unique=False
    )
    op.drop_index(
        op.f("ix_personal_tasks_user_created_at"), table_name="personal_tasks"
    )
    op.drop_index(
        op.f("ix_personal_tasks_user_updated_at"), table_name="personal_tasks"
    )
    op.create_index(
        op.f("ix_projects_deadline"), "projects", ["deadline"], unique=False
    )
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_index(op.f("ix_projects_deadline"), table_name="projects")
    op.create_index(
        op.f("ix_personal_tasks_user_updated_at"),
        "personal_tasks",
        ["user_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personal_tasks_user_created_at"),
        "personal_tasks",
        ["user_id", "created_at"],
        unique=False,
    )
    op.drop_index(op.f("ix_project_tasks_type"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_status"), table_name="project_tasks")
    op.drop_index("ix_project_tasks_project_type", table_name="project_tasks")
    op.drop_index("ix_project_tasks_project_status", table_name="project_tasks")
    op.drop_index("ix_project_tasks_project_priority", table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_project_id"), table_name="project_tasks")
    op.drop_index("ix_project_tasks_project_deadline", table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_priority"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_created_by_id"), table_name="project_tasks")
    op.drop_index(op.f("ix_project_tasks_assignee_id"), table_name="project_tasks")
    op.drop_table("project_tasks")
    # ### end Alembic commands ###
