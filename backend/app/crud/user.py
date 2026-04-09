"""用户 CRUD"""

from sqlalchemy.orm import Session

from ..core.security import get_password_hash, verify_password
from ..models.user import TeamRole, User


def get_user_by_username(db: Session, username: str) -> User | None:
    """按用户名查询用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """按主键查询用户"""
    return db.query(User).filter(User.id == user_id).first()


def list_users_in_team(db: Session, team_id: int) -> list[User]:
    """列出同小组成员（用于筛选下拉）"""
    return (
        db.query(User)
        .filter(User.team_id == team_id, User.is_active.is_(True))
        .order_by(User.username.asc())
        .all()
    )


def create_user(
    db: Session,
    username: str,
    password: str,
    *,
    team_id: int = 1,
    team_role: TeamRole = TeamRole.MEMBER,
) -> User:
    """创建用户（密码存哈希），并加入指定小组与该组下第一个项目"""
    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        team_id=team_id,
        team_role=team_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    from ..crud import project_member as pm_crud
    from ..models.project import Project
    from ..models.project_member import ProjectRole

    first_project = (
        db.query(Project)
        .filter(Project.team_id == team_id)
        .order_by(Project.id.asc())
        .first()
    )
    if first_project:
        pm_crud.upsert_member(db, first_project.id, user.id, ProjectRole.EDITOR)
    return user


def update_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
    """校验当前密码后更新为新密码，成功返回 True"""
    if not verify_password(current_password, user.hashed_password):
        return False
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return True
