"""审计日志查询"""

from typing import List, Tuple

from sqlalchemy import false, or_
from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..models.user import User


def list_for_team_and_user(
    db: Session,
    *,
    team_id: int,
    team_user_ids: List[int],
    team_project_ids: List[int],
    project_id: int | None,
    skip: int,
    limit: int,
) -> Tuple[List[AuditLog], int]:
    """
    组长：project_id 有值则只查该项目；无值则查本组项目相关 + 本组成员无 project_id 的操作。
    """
    _ = team_id  # 保留参数便于调用方语义清晰
    q = db.query(AuditLog)
    if project_id is not None:
        q = q.filter(AuditLog.project_id == project_id)
    else:
        conds = []
        if team_project_ids:
            conds.append(AuditLog.project_id.in_(team_project_ids))
        if team_user_ids:
            conds.append(
                (AuditLog.project_id.is_(None)) & (AuditLog.user_id.in_(team_user_ids))
            )
        if not conds:
            q = q.filter(false())
        else:
            q = q.filter(or_(*conds))
    total = q.count()
    rows = (
        q.order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
        .all()
    )
    return rows, total


def list_for_project(
    db: Session,
    *,
    project_id: int,
    skip: int,
    limit: int,
) -> Tuple[List[AuditLog], int]:
    """项目管理员：仅查看该项目相关日志。"""
    q = db.query(AuditLog).filter(AuditLog.project_id == project_id)
    total = q.count()
    rows = (
        q.order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
        .all()
    )
    return rows, total


def team_user_id_list(db: Session, team_id: int) -> List[int]:
    return [r[0] for r in db.query(User.id).filter(User.team_id == team_id).all()]


def team_project_id_list(db: Session, team_id: int) -> List[int]:
    from ..models.project import Project

    return [r[0] for r in db.query(Project.id).filter(Project.team_id == team_id).all()]
