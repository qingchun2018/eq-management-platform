"""teams, projects, project_members, project_id on tickets/tags, user team roles

Revision ID: b2c3d4e5f6a7
Revises: 9b3c4d5e6f7a
Create Date: 2026-04-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "9b3c4d5e6f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        raise RuntimeError("此迁移仅支持 PostgreSQL，请使用 PostgreSQL 数据库。")

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE teamrole AS ENUM ('TEAM_ADMIN', 'MEMBER', 'TEAM_VIEWER');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE projectrole AS ENUM ('PROJECT_ADMIN', 'EDITOR', 'VIEWER');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    teamrole_pg = postgresql.ENUM(
        "TEAM_ADMIN",
        "MEMBER",
        "TEAM_VIEWER",
        name="teamrole",
        create_type=False,
    )
    projectrole_pg = postgresql.ENUM(
        "PROJECT_ADMIN",
        "EDITOR",
        "VIEWER",
        name="projectrole",
        create_type=False,
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teams_id"), "teams", ["id"], unique=False)
    op.create_index("ix_teams_slug", "teams", ["slug"], unique=True)

    op.execute(
        "INSERT INTO teams (id, name, slug) VALUES "
        "(1, '默认小组', 'default'), (2, '小组二', 'team-b')"
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('teams', 'id'), (SELECT COALESCE(MAX(id), 1) FROM teams))"
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_team_id"), "projects", ["team_id"], unique=False)

    op.execute(
        "INSERT INTO projects (id, team_id, name, description) VALUES "
        "(1, 1, '默认项目', '历史数据迁移')"
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('projects', 'id'), (SELECT COALESCE(MAX(id), 1) FROM projects))"
    )

    op.add_column("tickets", sa.Column("project_id", sa.Integer(), nullable=True))
    op.add_column("tags", sa.Column("project_id", sa.Integer(), nullable=True))

    op.execute("UPDATE tickets SET project_id = 1 WHERE project_id IS NULL")
    op.execute("UPDATE tags SET project_id = 1 WHERE project_id IS NULL")

    op.alter_column("tickets", "project_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("tags", "project_id", existing_type=sa.Integer(), nullable=False)

    op.create_foreign_key(
        "fk_tickets_project_id_projects",
        "tickets",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_tags_project_id_projects",
        "tags",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_tickets_project_id"), "tickets", ["project_id"], unique=False)
    op.create_index(op.f("ix_tags_project_id"), "tags", ["project_id"], unique=False)

    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=False)
    op.create_unique_constraint("uq_tags_project_name", "tags", ["project_id", "name"])

    op.add_column("users", sa.Column("team_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("team_role", teamrole_pg, nullable=True))

    op.execute("UPDATE users SET team_id = 1, team_role = 'MEMBER' WHERE team_id IS NULL")

    op.create_foreign_key(
        "fk_users_team_id_teams",
        "users",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_users_team_id"), "users", ["team_id"], unique=False)

    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("role", projectrole_pg, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "project_id", name="uq_project_members_user_project"),
    )
    op.create_index(op.f("ix_project_members_id"), "project_members", ["id"], unique=False)
    op.create_index(op.f("ix_project_members_user_id"), "project_members", ["user_id"], unique=False)
    op.create_index(op.f("ix_project_members_project_id"), "project_members", ["project_id"], unique=False)

    op.execute(
        "INSERT INTO project_members (user_id, project_id, role) "
        "SELECT id, 1, 'EDITOR' FROM users"
    )


def downgrade() -> None:
    op.drop_table("project_members")
    op.drop_index(op.f("ix_users_team_id"), table_name="users")
    op.drop_constraint("fk_users_team_id_teams", "users", type_="foreignkey")
    op.drop_column("users", "team_role")
    op.drop_column("users", "team_id")

    op.drop_constraint("uq_tags_project_name", "tags", type_="unique")
    op.drop_constraint("fk_tags_project_id_projects", "tags", type_="foreignkey")
    op.drop_index(op.f("ix_tags_project_id"), table_name="tags")
    op.drop_column("tags", "project_id")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    op.drop_constraint("fk_tickets_project_id_projects", "tickets", type_="foreignkey")
    op.drop_index(op.f("ix_tickets_project_id"), table_name="tickets")
    op.drop_column("tickets", "project_id")

    op.drop_table("projects")
    op.drop_table("teams")

    op.execute("DROP TYPE IF EXISTS projectrole")
    op.execute("DROP TYPE IF EXISTS teamrole")
