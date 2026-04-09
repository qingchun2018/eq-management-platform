"""用户模型（登录与鉴权）"""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class TeamRole(str, enum.Enum):
    """小组级角色：组长管本组所有项目；组员按项目成员表；小组只读仅能浏览本组项目"""

    TEAM_ADMIN = "TEAM_ADMIN"
    MEMBER = "MEMBER"
    TEAM_VIEWER = "TEAM_VIEWER"


class User(Base):
    """系统用户"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), index=True)
    team_role = Column(
        Enum(TeamRole, name="teamrole", native_enum=True),
        nullable=True,
    )

    team = relationship("Team", back_populates="users")
    tickets_created = relationship("Ticket", back_populates="created_by")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
