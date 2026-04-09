"""测试夹具：覆盖 DB 依赖、创建测试用户/团队/项目、获取 auth header"""

import os

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog  # noqa: F401 — 注册 metadata 供 SQLite create_all
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.team import Team
from app.models.user import TeamRole, User
from app.core.security import get_password_hash, create_access_token

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    else:
        yield


@pytest.fixture(scope="function")
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        if "postgresql" in SQLALCHEMY_DATABASE_URL:
            session.execute(
                sa.text(
                    "TRUNCATE TABLE audit_logs, ticket_tags, tickets, tags, "
                    "project_members, projects, users, teams "
                    "RESTART IDENTITY CASCADE"
                )
            )
            session.commit()
        else:
            for table in reversed(Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        session.close()


def _seed_team_project_user(db_session):
    """创建测试用的小组、项目和用户，返回 (user, project, auth_headers)"""
    team = Team(id=1, name="测试小组", slug="test-team")
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    project = Project(id=1, team_id=team.id, name="测试项目")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass"),
        team_id=team.id,
        team_role=TeamRole.TEAM_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    pm = ProjectMember(user_id=user.id, project_id=project.id, role=ProjectRole.PROJECT_ADMIN)
    db_session.add(pm)
    db_session.commit()

    token = create_access_token(subject=user.username)
    headers = {"Authorization": f"Bearer {token}"}
    return user, project, headers


@pytest.fixture(scope="function")
def seeded(db):
    """返回 (user, project, headers) 三元组"""
    return _seed_team_project_user(db)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(client, seeded):
    """返回 (TestClient, user, project, headers)"""
    _, project, headers = seeded
    return client, project, headers
