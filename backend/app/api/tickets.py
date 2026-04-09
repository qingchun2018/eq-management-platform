from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from ..audit import log_action
from ..authz import can_read_project, can_write_ticket, resolve_effective_project_role
from ..crud import ticket as crud
from ..database import get_db
from ..deps import ProjectAccess, get_current_user, require_project_read
from ..models.user import User
from ..schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(get_current_user)],
)


def _parse_tag_ids(tag_ids: Optional[str]) -> Optional[list[int]]:
    if not tag_ids or not tag_ids.strip():
        return None
    try:
        return [int(x.strip()) for x in tag_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(
            status_code=400, detail="tag_ids 格式错误，应为逗号分隔的整数列表"
        )


def _assert_ticket_write(db: Session, user: User, ticket_id: int):
    t = crud.get_ticket(db, ticket_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    role = resolve_effective_project_role(db, user, t.project_id)
    if not can_read_project(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该 Ticket")
    if not can_write_ticket(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只读权限，无法修改")
    return t


@router.get("", response_model=TicketListResponse)
def list_tickets(
    status: Optional[str] = Query(None, description="状态过滤 (all/pending/completed)"),
    tag_ids: Optional[str] = Query(None, description="标签 ID 列表（逗号分隔）"),
    search: Optional[str] = Query(None, description="搜索关键词（标题与描述）"),
    created_by_user_id: Optional[int] = Query(None, description="创建人用户 ID"),
    sort_by: str = Query("created_at", description="排序字段: created_at / updated_at / title"),
    sort_order: str = Query("desc", description="排序方向: asc / desc"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    access: ProjectAccess = Depends(require_project_read),
):
    """获取某项目下的 Ticket 列表"""
    if sort_by not in ("created_at", "updated_at", "title"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sort_by 无效")
    if sort_order not in ("asc", "desc"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sort_order 无效")

    tag_id_list = _parse_tag_ids(tag_ids)
    tickets, total = crud.get_tickets(
        db,
        project_id=access.project_id,
        status=status,
        tag_ids=tag_id_list,
        search=search,
        created_by_user_id=created_by_user_id,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )

    return TicketListResponse(
        tickets=tickets,
        total=total,
        limit=limit,
        offset=skip,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个 Ticket"""
    t = crud.get_ticket(db, ticket_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    role = resolve_effective_project_role(db, current_user, t.project_id)
    if not can_read_project(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该 Ticket")
    return t


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 Ticket（须具备项目写权限）"""
    role = resolve_effective_project_role(db, current_user, ticket.project_id)
    if not can_write_ticket(role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权在该项目下创建 Ticket")
    created = crud.create_ticket(db, ticket, created_by_id=current_user.id)
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.create",
        resource_type="ticket",
        resource_id=created.id,
        project_id=created.project_id,
        detail={"title": created.title},
    )
    return created


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    ticket: TicketUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 Ticket"""
    _assert_ticket_write(db, current_user, ticket_id)
    updated_ticket = crud.update_ticket(db, ticket_id, ticket)
    if not updated_ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.update",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=updated_ticket.project_id,
        detail=ticket.model_dump(exclude_unset=True),
    )
    return updated_ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除 Ticket"""
    t = _assert_ticket_write(db, current_user, ticket_id)
    pid = t.project_id
    title = t.title
    success = crud.delete_ticket(db, ticket_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.delete",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=pid,
        detail={"title": title},
    )


@router.patch("/{ticket_id}/complete", response_model=TicketResponse)
def complete_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """完成 Ticket"""
    _assert_ticket_write(db, current_user, ticket_id)
    ticket = crud.complete_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.complete",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=ticket.project_id,
    )
    return ticket


@router.patch("/{ticket_id}/uncomplete", response_model=TicketResponse)
def uncomplete_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取消完成 Ticket"""
    _assert_ticket_write(db, current_user, ticket_id)
    ticket = crud.uncomplete_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.uncomplete",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=ticket.project_id,
    )
    return ticket


@router.post("/{ticket_id}/tags", response_model=TicketResponse)
def add_tags_to_ticket(
    ticket_id: int,
    request: Request,
    tag_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为 Ticket 添加标签"""
    _assert_ticket_write(db, current_user, ticket_id)
    ticket = crud.add_tags_to_ticket(db, ticket_id, tag_ids)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.tags.add",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=ticket.project_id,
        detail={"tag_ids": tag_ids},
    )
    return ticket


@router.delete("/{ticket_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_ticket(
    ticket_id: int,
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从 Ticket 移除标签"""
    t = _assert_ticket_write(db, current_user, ticket_id)
    pid = t.project_id
    ticket = crud.remove_tag_from_ticket(db, ticket_id, tag_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    log_action(
        db,
        request=request,
        user_id=current_user.id,
        username=current_user.username,
        action="ticket.tags.remove",
        resource_type="ticket",
        resource_id=ticket_id,
        project_id=pid,
        detail={"tag_id": tag_id},
    )
