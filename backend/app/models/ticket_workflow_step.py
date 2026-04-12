"""Ticket 顺序工作流步骤（多人按序处理，如数据流水线）"""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class WorkflowStepStatus(str, enum.Enum):
    """工作流步骤状态"""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class TicketWorkflowStep(Base):
    """单条 Ticket 下的一个顺序步骤，由指定负责人完成后流转到下一步"""

    __tablename__ = "ticket_workflow_steps"
    __table_args__ = (UniqueConstraint("ticket_id", "step_order", name="uq_ticket_workflow_step_order"),)

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    assignee_user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(
        Enum(WorkflowStepStatus, name="workflowstepstatus", native_enum=True),
        nullable=False,
        default=WorkflowStepStatus.PENDING,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="workflow_steps")
    assignee = relationship("User", foreign_keys=[assignee_user_id])

    def __repr__(self) -> str:
        return f"<TicketWorkflowStep(id={self.id}, ticket_id={self.ticket_id}, order={self.step_order})>"
