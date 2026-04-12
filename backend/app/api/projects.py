"""项目列表、创建与成员管理"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..audit import log_action
from ..authz import can_create_project, can_manage_project_members, can_read_project, resolve_effective_project_role
from ..crud import project as project_crud
from ..crud import project_member as pm_crud
from ..crud import ticket_workflow as ticket_workflow_crud
from ..crud import user as user_crud
from ..database import get_db
from ..deps import get_current_user
from ..models.project_member import ProjectRole
from ..models.user import User
from ..schemas.auth import UserPublic
from ..schemas.project import ProjectBrief, ProjectCreate, ProjectMemberCreate, ProjectMemberItem, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def _brief(db: Session, user: User, project_id: int) -> ProjectBrief:
    p = project_crud.get_project(db, project_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    r = resolve_effective_project_role(db, user, project_id)
    return ProjectBrief(
        id=p.id,
        team_id=p.team_id,
        name=p.name,
        description=p.description,
        my_role=r.value if r else "VIEWER",
    )


@router.get("", response_model=List[ProjectBrief])
def list_my_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出当前用户可访问的本组项目及在项目内的有效角色"""
    ps = project_crud.list_accessible_projects(db, user)
    return [_brief(db, user, p.id) for p in ps]


@router.post("", response_model=ProjectBrief, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """在本小组下新建项目（仅组长）"""
    if not can_create_project(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅组长可新建项目")
    if user.team_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户未归属小组")
    p = project_crud.create_project(db, user.team_id, body.name, body.description)
    pm_crud.add_editor_for_new_project(db, p.id, user.id)
    log_action(
        db,
        request=request,
        user_id=user.id,
        username=user.username,
        action="project.create",
        resource_type="project",
        resource_id=p.id,
        project_id=p.id,
        detail={"name": body.name},
    )
    return _brief(db, user, p.id)


@router.get("/{project_id}/workflow-assignees", response_model=List[UserPublic])
def list_workflow_assignees(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出可作为工作流步骤负责人的本组成员（须有项目读权限）"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_read_project(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该项目")
    users = ticket_workflow_crud.list_assignable_users_for_project(db, project_id)
    return [UserPublic(id=u.id, username=u.username) for u in users]


@router.get("/{project_id}", response_model=ProjectBrief)
def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """查看项目详情（须有项目读权限）"""
    role = resolve_effective_project_role(db, user, project_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该项目")
    return _brief(db, user, project_id)


@router.patch("/{project_id}", response_model=ProjectBrief)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """编辑项目名称/描述（仅项目管理员或组长）"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_manage_project_members(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅项目管理员或组长可编辑项目")
    updated = project_crud.update_project(db, project_id, body.name, body.description)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    log_action(
        db,
        request=request,
        user_id=user.id,
        username=user.username,
        action="project.update",
        resource_type="project",
        resource_id=project_id,
        project_id=project_id,
        detail=body.model_dump(exclude_unset=True),
    )
    return _brief(db, user, project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除项目（仅组长）"""
    if not can_create_project(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅组长可删除项目")
    existing = project_crud.get_project(db, project_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    log_action(
        db,
        request=request,
        user_id=user.id,
        username=user.username,
        action="project.delete",
        resource_type="project",
        resource_id=project_id,
        project_id=project_id,
        detail={"name": existing.name},
    )
    project_crud.delete_project(db, project_id)


@router.get("/{project_id}/members", response_model=List[ProjectMemberItem])
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出项目成员（项目管理员或组长）"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_manage_project_members(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要项目管理员或组长权限")
    rows = pm_crud.list_members(db, project_id)
    out: List[ProjectMemberItem] = []
    for row in rows:
        u = user_crud.get_user_by_id(db, row.user_id)
        if not u:
            continue
        out.append(
            ProjectMemberItem(
                user=UserPublic(id=u.id, username=u.username),
                role=row.role.value,
            )
        )
    return out


@router.post("/{project_id}/members", response_model=ProjectMemberItem, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    body: ProjectMemberCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """添加或更新项目成员角色（须同小组）"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_manage_project_members(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要项目管理员或组长权限")
    target = user_crud.get_user_by_id(db, body.user_id)
    if not target or target.team_id != user.team_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只能添加本小组成员")
    try:
        pr = ProjectRole(body.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="role 无效")
    row = pm_crud.upsert_member(db, project_id, body.user_id, pr)
    u = user_crud.get_user_by_id(db, row.user_id)
    assert u is not None
    log_action(
        db,
        request=request,
        user_id=user.id,
        username=user.username,
        action="project.member.upsert",
        resource_type="project_member",
        resource_id=body.user_id,
        project_id=project_id,
        detail={"target_username": u.username, "role": row.role.value},
    )
    return ProjectMemberItem(user=UserPublic(id=u.id, username=u.username), role=row.role.value)


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """从项目移除成员"""
    role = resolve_effective_project_role(db, user, project_id)
    if not can_manage_project_members(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要项目管理员或组长权限")
    if user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除本人")
    target = user_crud.get_user_by_id(db, user_id)
    ok = pm_crud.remove_member(db, project_id, user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    log_action(
        db,
        request=request,
        user_id=user.id,
        username=user.username,
        action="project.member.remove",
        resource_type="project_member",
        resource_id=user_id,
        project_id=project_id,
        detail={"removed_username": target.username if target else None},
    )
