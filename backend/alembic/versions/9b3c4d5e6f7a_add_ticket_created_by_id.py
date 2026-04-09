"""add created_by_id to tickets

Revision ID: 9b3c4d5e6f7a
Revises: 8f4a2c1b0d3e
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "9b3c4d5e6f7a"
down_revision: Union[str, Sequence[str], None] = "8f4a2c1b0d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tickets", sa.Column("created_by_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_tickets_created_by_id"), "tickets", ["created_by_id"], unique=False)
    op.create_foreign_key(
        "fk_tickets_created_by_id_users",
        "tickets",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tickets_created_by_id_users", "tickets", type_="foreignkey")
    op.drop_index(op.f("ix_tickets_created_by_id"), table_name="tickets")
    op.drop_column("tickets", "created_by_id")
