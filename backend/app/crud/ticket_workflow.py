"""Ticket 顺序工作流 CRUD 与校验"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy.orm import Session, joinedload

from ..models.project import Project
from ..models.project_member import ProjectMember, ProjectRole
from ..models.ticket import Ticket, TicketStatus
from ..models.ticket_workflow_step import TicketWorkflowStep, WorkflowStepStatus
from ..models.user import TeamRole, User
from ..schemas.ticket import WorkflowStepCreateItem

MAX_WORKFLOW_STEPS = 30


def list_assignable_users_for_project(db: Session, project_id: int) -> List[User]:
    """
    可作为工作流步骤负责人的用户：项目内 EDITOR/PROJECT_ADMIN，
    以及本小组组长（组长对本组项目均有管理权，可作为任一步负责人）。
    排除仅 VIEWER 的项目成员（只读不适合承接处理步骤）。
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        return []

    member_rows: Sequence[ProjectMember] = (
        db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    )
    seen: set[int] = set()
    out: List[User] = []

    for m in member_rows:
        if m.role == ProjectRole.VIEWER:
            continue
        u = db.query(User).filter(User.id == m.user_id).first()
        if u and u.id not in seen:
            seen.add(u.id)
            out.append(u)

    admins = (
        db.query(User)
        .filter(User.team_id == proj.team_id, User.team_role == TeamRole.TEAM_ADMIN)
        .all()
    )
    for u in admins:
        if u.id not in seen:
            seen.add(u.id)
            out.append(u)

    out.sort(key=lambda x: x.username.lower())
    return out


def user_id_assignable_for_project(db: Session, project_id: int, user_id: int) -> bool:
    allowed = {u.id for u in list_assignable_users_for_project(db, project_id)}
    return user_id in allowed


def create_workflow_steps_for_ticket(
    db: Session,
    ticket: Ticket,
    items: Sequence[WorkflowStepCreateItem],
) -> None:
    if not items:
        return
    if len(items) > MAX_WORKFLOW_STEPS:
        raise ValueError(f"工作流步骤最多 {MAX_WORKFLOW_STEPS} 步")

    pid = ticket.project_id
    for i, item in enumerate(items, start=1):
        if not user_id_assignable_for_project(db, pid, item.assignee_user_id):
            raise ValueError(f"步骤「{item.name}」的负责人无权作为该项目工作流处理人")

        st = WorkflowStepStatus.IN_PROGRESS if i == 1 else WorkflowStepStatus.PENDING
        row = TicketWorkflowStep(
            ticket_id=ticket.id,
            step_order=i,
            name=item.name.strip(),
            assignee_user_id=item.assignee_user_id,
            status=st,
        )
        db.add(row)
    db.flush()


def load_ticket_with_workflow(db: Session, ticket_id: int) -> Optional[Ticket]:
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


def sorted_workflow_steps(ticket: Ticket) -> List[TicketWorkflowStep]:
    return sorted(ticket.workflow_steps, key=lambda s: s.step_order)


def complete_workflow_step(
    db: Session,
    ticket_id: int,
    step_id: int,
    user: User,
    completion_note: Optional[str],
) -> Optional[Ticket]:
    """
    将指定步骤标为完成，并激活下一步；若已是最后一步则标记 Ticket 完成。
    负责人本人或项目管理员/组长可完成当前进行中步骤。
    """
    ticket = load_ticket_with_workflow(db, ticket_id)
    if not ticket:
        return None

    steps = sorted_workflow_steps(ticket)
    step = next((s for s in steps if s.id == step_id), None)
    if not step:
        return None

    if step.status != WorkflowStepStatus.IN_PROGRESS:
        raise ValueError("只能完成当前进行中的步骤")

    from ..authz import can_manage_project_members, resolve_effective_project_role

    role = resolve_effective_project_role(db, user, ticket.project_id)
    is_project_admin = can_manage_project_members(role)

    if user.id != step.assignee_user_id and not is_project_admin:
        raise ValueError("仅该步负责人或项目管理员可完成此步骤")

    step.status = WorkflowStepStatus.COMPLETED
    step.completed_at = datetime.now(timezone.utc)
    if completion_note and completion_note.strip():
        step.completion_note = completion_note.strip()[:10000]

    next_step = next((s for s in steps if s.step_order == step.step_order + 1), None)
    if next_step:
        next_step.status = WorkflowStepStatus.IN_PROGRESS
    else:
        ticket.status = TicketStatus.COMPLETED
        ticket.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)
    return load_ticket_with_workflow(db, ticket_id)


def ticket_has_incomplete_workflow(db: Session, ticket_id: int) -> bool:
    n = (
        db.query(TicketWorkflowStep)
        .filter(
            TicketWorkflowStep.ticket_id == ticket_id,
            TicketWorkflowStep.status != WorkflowStepStatus.COMPLETED,
        )
        .count()
    )
    return n > 0
