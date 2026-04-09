"""项目成员维护"""

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.project_member import ProjectMember, ProjectRole


def get_membership(db: Session, user_id: int, project_id: int) -> Optional[ProjectMember]:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == user_id, ProjectMember.project_id == project_id)
        .first()
    )


def list_members(db: Session, project_id: int) -> List[ProjectMember]:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()


def upsert_member(
    db: Session,
    project_id: int,
    user_id: int,
    role: ProjectRole,
) -> ProjectMember:
    row = get_membership(db, user_id, project_id)
    if row:
        row.role = role
    else:
        row = ProjectMember(user_id=user_id, project_id=project_id, role=role)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def remove_member(db: Session, project_id: int, user_id: int) -> bool:
    row = get_membership(db, user_id, project_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def add_editor_for_new_project(db: Session, project_id: int, user_id: int) -> None:
    """新建项目后，创建人自动加入为项目管理员"""
    upsert_member(db, project_id, user_id, ProjectRole.PROJECT_ADMIN)
