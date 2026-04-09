from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..audit import log_action
from ..authz import can_manage_tags, can_read_project, resolve_effective_project_role
from ..crud import tag as crud
from ..database import get_db
from ..deps import ProjectAccess, get_current_user, require_project_read
from ..models.tag import Tag, ticket_tags
from ..models.user import User
from ..schemas.tag import TagCreate, TagListResponse, TagResponse, TagUpdate

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    dependencies=[Depends(get_current_user)],
)


def _assert_tag_write(db: Session, user: User, tag_id: int) -> Tag:
    tag = crud.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    role = resolve_effective_project_role(db, user, tag.project_id)
    if not can_manage_tags(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改标签")
    return tag


@router.get("", response_model=TagListResponse)
def list_tags(
    db: Session = Depends(get_db),
    access: ProjectAccess = Depends(require_project_read),
):
    """获取某项目下所有标签（单次查询含 ticket_count）"""
    rows = (
        db.query(Tag, func.count(ticket_tags.c.ticket_id).label("cnt"))
        .outerjoin(ticket_tags, ticket_tags.c.tag_id == Tag.id)
        .filter(Tag.project_id == access.project_id)
        .group_by(Tag.id)
        .order_by(Tag.id.asc())
        .all()
    )

    tag_responses = [
        {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "created_at": tag.created_at,
            "ticket_count": cnt,
        }
        for tag, cnt in rows
    ]

    return TagListResponse(tags=tag_responses, total=len(tag_responses))


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个标签"""
    tag = crud.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    role = resolve_effective_project_role(db, current_user, tag.project_id)
    if not can_read_project(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该标签")

    ticket_count = (
        db.query(func.count(ticket_tags.c.ticket_id))
        .filter(ticket_tags.c.tag_id == tag.id)
        .scalar()
    )

    return TagResponse(
        id=tag.id,
        name=tag.name,
        color=tag.color,
        created_at=tag.created_at,
        ticket_count=ticket_count,
    )


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    body: TagUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新标签名称或颜色"""
    existing = crud.get_tag(db, tag_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    _assert_tag_write(db, current_user, tag_id)

    if body.name is not None and body.name != existing.name:
        name_taken = crud.get_tag_by_name(db, existing.project_id, body.name)
        if name_taken and name_taken.id != tag_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该名称已被其他标签使用",
            )
    if body.name is None and body.color is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少提供 name 或 color")

    updated = crud.update_tag(db, tag_id, body.name, body.color)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    ticket_count = (
        db.query(func.count(ticket_tags.c.ticket_id))
        .filter(ticket_tags.c.tag_id == updated.id)
        .scalar()
    )
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="tag.update",
        resource_type="tag",
        resource_id=tag_id,
        project_id=updated.project_id,
        detail=body.model_dump(exclude_unset=True),
    )
    return TagResponse(
        id=updated.id,
        name=updated.name,
        color=updated.color,
        created_at=updated.created_at,
        ticket_count=ticket_count,
    )


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: TagCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新标签"""
    role = resolve_effective_project_role(db, current_user, tag.project_id)
    if not can_manage_tags(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权在该项目下创建标签")

    existing_tag = crud.get_tag_by_name(db, tag.project_id, tag.name)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该项目下已存在同名标签",
        )

    new_tag = crud.create_tag(db, tag)
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="tag.create",
        resource_type="tag",
        resource_id=new_tag.id,
        project_id=new_tag.project_id,
        detail={"name": new_tag.name},
    )
    return TagResponse(
        id=new_tag.id,
        name=new_tag.name,
        color=new_tag.color,
        created_at=new_tag.created_at,
        ticket_count=0,
    )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除标签"""
    tg = _assert_tag_write(db, current_user, tag_id)
    pid = tg.project_id
    name = tg.name
    success = crud.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="tag.delete",
        resource_type="tag",
        resource_id=tag_id,
        project_id=pid,
        detail={"name": name},
    )
