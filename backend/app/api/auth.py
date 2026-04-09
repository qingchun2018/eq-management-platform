"""登录、注册、刷新令牌、修改密码与用户列表"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..audit import log_action
from ..config import settings
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from ..authz import resolve_effective_project_role
from ..crud import project as project_crud
from ..crud import user as user_crud
from ..database import get_db
from ..deps import get_current_user
from ..limiter import limiter
from ..models.team import Team
from ..models.user import User
from ..schemas.auth import (
    PasswordChange,
    RefreshRequest,
    Token,
    UserPublic,
    UserRegister,
)
from ..schemas.project import MeResponse, ProjectBrief, TeamBrief

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> Token:
    """签发 access + refresh"""
    access_token = create_access_token(subject=user.username)
    refresh_token = create_refresh_token(subject=user.username)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH_LOGIN)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """OAuth2 密码模式登录，返回 JWT（Swagger 中可直接 Authorize）"""
    user = user_crud.get_user_by_username(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH_REFRESH)
def refresh_tokens(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """使用 refresh_token 换取新的 access_token 与 refresh_token"""
    username = decode_refresh_token(body.refresh_token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")
    user = user_crud.get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    return _issue_tokens(user)


@router.get("/me", response_model=MeResponse)
def read_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户信息、所属小组、可访问项目及项目内角色"""
    team_brief = None
    if current_user.team_id:
        t = db.query(Team).filter(Team.id == current_user.team_id).first()
        if t:
            team_brief = TeamBrief.model_validate(t)
    projects = project_crud.list_accessible_projects(db, current_user)
    pb: list[ProjectBrief] = []
    for p in projects:
        r = resolve_effective_project_role(db, current_user, p.id)
        pb.append(
            ProjectBrief(
                id=p.id,
                team_id=p.team_id,
                name=p.name,
                description=p.description,
                my_role=r.value if r else "VIEWER",
            )
        )
    return MeResponse(
        id=current_user.id,
        username=current_user.username,
        team=team_brief,
        team_role=current_user.team_role.value if current_user.team_role else None,
        projects=pb,
    )


@router.get("/users", response_model=List[UserPublic])
def list_users_for_filter(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出本小组活跃用户（用于 Ticket 创建人筛选等）"""
    if current_user.team_id is None:
        return []
    users = user_crud.list_users_in_team(db, current_user.team_id)
    return [UserPublic(id=u.id, username=u.username) for u in users]


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH_REGISTER)
def register(
    request: Request,
    body: UserRegister,
    db: Session = Depends(get_db),
):
    """自助注册（需配置 AUTH_ALLOW_REGISTER=true）"""
    if not settings.AUTH_ALLOW_REGISTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="未开放注册")
    existing = user_crud.get_user_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = user_crud.create_user(db, body.username, body.password)
    return UserPublic(id=user.id, username=user.username)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.RATE_LIMIT_AUTH_CHANGE_PASSWORD)
def change_password(
    request: Request,
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改当前用户密码"""
    ok = user_crud.update_password(db, current_user, body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码不正确")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="auth.password.change",
        resource_type="user",
        resource_id=current_user.id,
        project_id=None,
    )
