"""审计日志查询（组长或项目管理员）"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..authz import can_view_audit_logs
from ..crud import audit_log as audit_crud
from ..database import get_db
from ..deps import get_current_user
from ..models.user import TeamRole, User
from ..schemas.audit import AuditLogItem, AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    project_id: int | None = Query(None, description="按项目筛选；项目管理员必填"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出审计记录（组长可看本组；项目管理员仅指定 project_id）"""
    if not can_view_audit_logs(db, user, project_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看审计日志")

    if user.team_role == TeamRole.TEAM_ADMIN:
        if user.team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户未归属小组",
            )
        uids = audit_crud.team_user_id_list(db, user.team_id)
        pids = audit_crud.team_project_id_list(db, user.team_id)
        rows, total = audit_crud.list_for_team_and_user(
            db,
            team_id=user.team_id,
            team_user_ids=uids,
            team_project_ids=pids,
            project_id=project_id,
            skip=skip,
            limit=limit,
        )
    else:
        if project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="项目管理员须指定 project_id",
            )
        rows, total = audit_crud.list_for_project(
            db, project_id=project_id, skip=skip, limit=limit
        )

    items: List[AuditLogItem] = []
    for r in rows:
        items.append(
            AuditLogItem(
                id=r.id,
                username=r.username,
                action=r.action,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                project_id=r.project_id,
                detail=r.detail,
                request_id=r.request_id,
                created_at=r.created_at,
            )
        )
    return AuditLogListResponse(items=items, total=total, skip=skip, limit=limit)
