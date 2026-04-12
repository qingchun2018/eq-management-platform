from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..models.tag import Tag, ticket_tags
from ..models.ticket import Ticket, TicketStatus
from ..models.ticket_workflow_step import TicketWorkflowStep
from ..schemas.ticket import TicketCreate, TicketUpdate
from ..utils.search_escape import escape_ilike_pattern


def get_tickets(
    db: Session,
    project_id: int,
    status: Optional[str] = None,
    tag_ids: Optional[List[int]] = None,
    search: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Ticket], int]:
    """获取某项目下的 Ticket 列表"""
    query = db.query(Ticket).filter(Ticket.project_id == project_id)

    if status and status != "all":
        status_upper = status.upper()
        if status_upper == "PENDING":
            query = query.filter(Ticket.status == TicketStatus.PENDING)
        elif status_upper == "COMPLETED":
            query = query.filter(Ticket.status == TicketStatus.COMPLETED)

    if tag_ids:
        query = query.filter(
            Ticket.id.in_(
                db.query(ticket_tags.c.ticket_id)
                .filter(ticket_tags.c.tag_id.in_(tag_ids))
                .distinct()
            )
        )

    if created_by_user_id is not None:
        query = query.filter(Ticket.created_by_id == created_by_user_id)

    if search and search.strip():
        esc = escape_ilike_pattern(search.strip())
        pattern = f"%{esc}%"
        query = query.filter(
            or_(
                Ticket.title.ilike(pattern, escape="\\"),
                Ticket.description.ilike(pattern, escape="\\"),
            )
        )

    total = query.count()

    sort_map = {
        "created_at": Ticket.created_at,
        "updated_at": Ticket.updated_at,
        "title": Ticket.title,
    }
    col = sort_map.get(sort_by, Ticket.created_at)
    order_col = col.desc() if sort_order == "desc" else col.asc()
    tickets = (
        query.options(
            joinedload(Ticket.created_by),
            joinedload(Ticket.tags),
            joinedload(Ticket.workflow_steps).joinedload(TicketWorkflowStep.assignee),
        )
        .order_by(order_col)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return tickets, total


def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    return (
        db.query(Ticket)
        .options(
            joinedload(Ticket.created_by),
            joinedload(Ticket.tags),
            joinedload(Ticket.workflow_steps).joinedload(TicketWorkflowStep.assignee),
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )


def create_ticket(db: Session, ticket: TicketCreate, created_by_id: Optional[int]) -> Ticket:
    db_ticket = Ticket(
        project_id=ticket.project_id,
        title=ticket.title,
        description=ticket.description,
        created_by_id=created_by_id,
    )
    db.add(db_ticket)
    db.flush()

    if ticket.tag_ids:
        tags = (
            db.query(Tag)
            .filter(Tag.id.in_(ticket.tag_ids), Tag.project_id == ticket.project_id)
            .all()
        )
        db_ticket.tags = tags

    if ticket.workflow_steps:
        from . import ticket_workflow as wf

        wf.create_workflow_steps_for_ticket(db, db_ticket, ticket.workflow_steps)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket: TicketUpdate) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    if ticket.title is not None:
        db_ticket.title = ticket.title
    if ticket.description is not None:
        db_ticket.description = ticket.description
    if ticket.tag_ids is not None:
        tags = (
            db.query(Tag)
            .filter(Tag.id.in_(ticket.tag_ids), Tag.project_id == db_ticket.project_id)
            .all()
        )
        db_ticket.tags = tags

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False

    db.delete(db_ticket)
    db.commit()
    return True


def complete_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    from .ticket_workflow import ticket_has_incomplete_workflow

    if ticket_has_incomplete_workflow(db, ticket_id):
        raise ValueError("存在未完成的工作流步骤，请按顺序完成各步")

    db_ticket.status = TicketStatus.COMPLETED
    db_ticket.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def uncomplete_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    wf_count = (
        db.query(TicketWorkflowStep).filter(TicketWorkflowStep.ticket_id == ticket_id).count()
    )
    if wf_count > 0:
        raise ValueError("已启用工作流的 Ticket 不支持一键取消完成，请由管理员在库中调整步骤数据")

    db_ticket.status = TicketStatus.PENDING
    db_ticket.completed_at = None
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def add_tags_to_ticket(db: Session, ticket_id: int, tag_ids: List[int]) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    tags = (
        db.query(Tag)
        .filter(Tag.id.in_(tag_ids), Tag.project_id == db_ticket.project_id)
        .all()
    )
    existing_tag_ids = {tag.id for tag in db_ticket.tags}

    for tag in tags:
        if tag.id not in existing_tag_ids:
            db_ticket.tags.append(tag)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def remove_tag_from_ticket(db: Session, ticket_id: int, tag_id: int) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    db_ticket.tags = [tag for tag in db_ticket.tags if tag.id != tag_id]
    db.commit()
    db.refresh(db_ticket)
    return db_ticket
