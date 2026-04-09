"""项目与小组查询"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.project import Project
from ..models.project_member import ProjectMember
from ..models.user import TeamRole, User


def get_project(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def list_projects_in_team(db: Session, team_id: int) -> List[Project]:
    return db.query(Project).filter(Project.team_id == team_id).order_by(Project.id.asc()).all()


def list_accessible_projects(db: Session, user: User) -> List[Project]:
    """当前用户可见的本组项目列表"""
    if user.team_id is None:
        return []
    q = db.query(Project).filter(Project.team_id == user.team_id)
    if user.team_role in (TeamRole.TEAM_ADMIN, TeamRole.TEAM_VIEWER):
        return q.order_by(Project.id.asc()).all()
    if user.team_role == TeamRole.MEMBER:
        return (
            q.join(ProjectMember, ProjectMember.project_id == Project.id)
            .filter(ProjectMember.user_id == user.id)
            .order_by(Project.id.asc())
            .all()
        )
    return []


def create_project(db: Session, team_id: int, name: str, description: Optional[str]) -> Project:
    p = Project(team_id=team_id, name=name, description=description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def update_project(
    db: Session, project_id: int, name: Optional[str], description: Optional[str]
) -> Optional[Project]:
    p = get_project(db, project_id)
    if not p:
        return None
    if name is not None:
        p.name = name
    if description is not None:
        p.description = description
    db.commit()
    db.refresh(p)
    return p


def delete_project(db: Session, project_id: int) -> bool:
    p = get_project(db, project_id)
    if not p:
        return False
    db.delete(p)
    db.commit()
    return True
