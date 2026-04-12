"""ticket_workflow_steps 顺序工作流步骤表

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 单独创建 ENUM，建表时 create_type=False，避免 SQLAlchemy 再次发出 CREATE TYPE（与 DO 块重复导致 DuplicateObject）
_workflow_step_status = postgresql.ENUM(
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    name="workflowstepstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    _workflow_step_status.create(bind, checkfirst=True)

    op.create_table(
        "ticket_workflow_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("assignee_user_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            _workflow_step_status,
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", "step_order", name="uq_ticket_workflow_step_order"),
    )
    op.create_index(op.f("ix_ticket_workflow_steps_id"), "ticket_workflow_steps", ["id"], unique=False)
    op.create_index(
        op.f("ix_ticket_workflow_steps_ticket_id"), "ticket_workflow_steps", ["ticket_id"], unique=False
    )
    op.create_index(
        op.f("ix_ticket_workflow_steps_assignee_user_id"),
        "ticket_workflow_steps",
        ["assignee_user_id"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.drop_index(op.f("ix_ticket_workflow_steps_assignee_user_id"), table_name="ticket_workflow_steps")
    op.drop_index(op.f("ix_ticket_workflow_steps_ticket_id"), table_name="ticket_workflow_steps")
    op.drop_index(op.f("ix_ticket_workflow_steps_id"), table_name="ticket_workflow_steps")
    op.drop_table("ticket_workflow_steps")
    op.execute(sa.text("DROP TYPE IF EXISTS workflowstepstatus"))
