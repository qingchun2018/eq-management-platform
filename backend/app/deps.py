"""FastAPI 依赖：当前登录用户、项目权限等"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .authz import (
    can_read_project,
    can_write_ticket,
    resolve_effective_project_role,
)
from .config import settings
from .core.security import decode_access_token
from .crud import user as user_crud
from .database import get_db
from .models.project_member import ProjectRole
from .models.user import User

# OpenAPI 与 Swagger 中「Authorize」使用的 token 端点
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """从 Bearer Token 解析并加载当前用户；无效则 401"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = decode_access_token(token)
    if username is None:
        raise credentials_exception
    user = user_crud.get_user_by_username(db, username=username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@dataclass
class ProjectAccess:
    """当前请求上下文：项目 ID + 有效项目角色 + 用户"""

    project_id: int
    role: ProjectRole
    user: User


def require_project_read(
    project_id: int = Query(..., description="项目 ID"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectAccess:
    """校验对项目的读权限（浏览 Ticket/标签列表）"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_read_project(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该项目")
    return ProjectAccess(project_id=project_id, role=role, user=user)


def require_project_write(
    project_id: int = Query(..., description="项目 ID"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectAccess:
    """校验编辑 Ticket、增改标签等写权限"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_write_ticket(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只读或无权限，无法修改")
    return ProjectAccess(project_id=project_id, role=role, user=user)
