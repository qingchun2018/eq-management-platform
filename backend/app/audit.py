"""审计日志写入工具"""

import json
import logging
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from .models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    *,
    request: Request | None = None,
    user_id: int | None = None,
    username: str | None = None,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    project_id: int | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """写入一条审计日志"""
    ip = None
    req_id = None
    if request is not None:
        ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else None)
        req_id = getattr(request.state, "request_id", None)

    entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        project_id=project_id,
        detail=json.dumps(detail, ensure_ascii=False, default=str) if detail else None,
        ip_address=ip,
        request_id=req_id,
    )
    try:
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("审计日志写入失败", exc_info=True)
