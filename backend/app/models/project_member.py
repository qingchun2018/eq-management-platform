"""用户在项目内的角色（组员按项目区分权限）"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ProjectRole(str, enum.Enum):
    """项目内角色：管理员可管成员与标签；编辑可改 Ticket；只读仅能查看"""

    PROJECT_ADMIN = "PROJECT_ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class ProjectMember(Base):
    """用户与项目的关联及项目级角色"""

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("user_id", "project_id", name="uq_project_members_user_project"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        Enum(ProjectRole, name="projectrole", native_enum=True),
        nullable=False,
        default=ProjectRole.EDITOR,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="project_memberships")
    project = relationship("Project", back_populates="members")
