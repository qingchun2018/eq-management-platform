"""项目与小组级权限判断"""

from typing import Dict, List

from sqlalchemy.orm import Session

from .models.project import Project
from .models.project_member import ProjectMember, ProjectRole
from .models.user import TeamRole, User


def resolve_effective_project_role(db: Session, user: User, project_id: int) -> ProjectRole | None:
    """
    解析用户在某项目下的有效角色。
    - 组长(TEAM_ADMIN)：等价于项目管理员，可操作本组内所有项目。
    - 小组只读(TEAM_VIEWER)：仅能只读浏览本组内所有项目。
    - 组员(MEMBER)：以 project_members 表为准；无记录则无权限。
    """
    if user.team_id is None:
        return None
    proj = db.query(Project).filter(Project.id == project_id).first()
    if proj is None or proj.team_id != user.team_id:
        return None

    if user.team_role == TeamRole.TEAM_ADMIN:
        return ProjectRole.PROJECT_ADMIN
    if user.team_role == TeamRole.TEAM_VIEWER:
        return ProjectRole.VIEWER

    # MEMBER 或 team_role 为 NULL / 其他值：以 project_members 表为准
    pm = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.user_id == user.id,
            ProjectMember.project_id == project_id,
        )
        .first()
    )
    return pm.role if pm else None


def batch_resolve_effective_project_roles(
    db: Session, user: User, projects: List[Project]
) -> Dict[int, ProjectRole | None]:
    """
    批量解析用户在多个项目下的有效角色，语义与逐条调用 resolve_effective_project_role 一致。
    用于 /auth/me 等路径，避免对每个项目单独查库（N+1）。
    """
    if user.team_id is None or not projects:
        return {}
    out: Dict[int, ProjectRole | None] = {}
    valid = [p for p in projects if p.team_id == user.team_id]

    if user.team_role == TeamRole.TEAM_ADMIN:
        for p in valid:
            out[p.id] = ProjectRole.PROJECT_ADMIN
    elif user.team_role == TeamRole.TEAM_VIEWER:
        for p in valid:
            out[p.id] = ProjectRole.VIEWER
    elif valid:
        ids = [p.id for p in valid]
        rows = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.user_id == user.id,
                ProjectMember.project_id.in_(ids),
            )
            .all()
        )
        pm_by_pid = {r.project_id: r.role for r in rows}
        for p in valid:
            out[p.id] = pm_by_pid.get(p.id)

    for p in projects:
        if p.id not in out:
            out[p.id] = None
    return out


def can_read_project(role: ProjectRole | None) -> bool:
    """是否可查看项目内 Ticket/标签"""
    return role is not None


def can_write_ticket(role: ProjectRole | None) -> bool:
    """是否可创建/编辑/完成 Ticket"""
    return role in (ProjectRole.PROJECT_ADMIN, ProjectRole.EDITOR)


def can_manage_tags(role: ProjectRole | None) -> bool:
    """是否可创建/编辑/删除标签（项目内）"""
    return role in (ProjectRole.PROJECT_ADMIN, ProjectRole.EDITOR)


def can_manage_project_members(role: ProjectRole | None) -> bool:
    """是否可管理项目成员（仅项目管理员或组长）"""
    return role == ProjectRole.PROJECT_ADMIN


def can_create_project(user: User) -> bool:
    """是否可在本小组下新建项目（仅组长）"""
    return user.team_id is not None and user.team_role == TeamRole.TEAM_ADMIN


def can_view_audit_logs(db: Session, user: User, project_id: int | None) -> bool:
    """
    查看审计日志：组长可看本组范围；项目管理员仅能在指定 project_id 下查看。
    project_id 为 None 时仅组长允许（查整组）。
    """
    if user.team_id is None:
        return False
    if user.team_role == TeamRole.TEAM_ADMIN:
        if project_id is None:
            return True
        proj = db.query(Project).filter(Project.id == project_id).first()
        return proj is not None and proj.team_id == user.team_id
    if project_id is None:
        return False
    role = resolve_effective_project_role(db, user, project_id)
    return role == ProjectRole.PROJECT_ADMIN
