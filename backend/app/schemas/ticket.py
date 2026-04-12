from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .auth import UserPublic
from .tag import TagResponse


class WorkflowStepCreateItem(BaseModel):
    """创建工作流中的一步"""

    name: str = Field(..., min_length=1, max_length=128, description="步骤名称，如：数据爬虫、数据清洗")
    assignee_user_id: int = Field(..., description="该步负责人用户 ID")


class WorkflowStepCompleteBody(BaseModel):
    """完成某工作流步骤时的可选备注"""

    completion_note: Optional[str] = Field(None, max_length=10000, description="完成说明（可选）")


class WorkflowStepResponse(BaseModel):
    """工作流步骤（返回）"""

    id: int
    step_order: int
    name: str
    status: str
    assignee: UserPublic
    completed_at: Optional[datetime] = None
    completion_note: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_step_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        if hasattr(v, "value"):
            return v.value.lower()
        return str(v).lower()

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    """Ticket 基础模型"""

    title: str = Field(..., min_length=1, max_length=255, description="Ticket 标题")
    description: Optional[str] = Field(None, max_length=10000, description="Ticket 描述")


class TicketCreate(TicketBase):
    """创建 Ticket 请求模型"""

    project_id: int = Field(..., description="所属项目 ID")
    tag_ids: Optional[List[int]] = Field(default_factory=list, description="标签 ID 列表")
    workflow_steps: Optional[List[WorkflowStepCreateItem]] = Field(
        default=None,
        description="可选：顺序工作流步骤（至少 2 步时体现多人接力；每步指定负责人）",
    )


class TicketUpdate(BaseModel):
    """更新 Ticket 请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    tag_ids: Optional[List[int]] = Field(None, description="若提供则覆盖 Ticket 的标签集合")


class TicketResponse(TicketBase):
    """Ticket 响应模型"""

    id: int
    project_id: int
    status: str
    tags: List[TagResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[UserPublic] = None
    workflow_steps: List[WorkflowStepResponse] = Field(default_factory=list, description="顺序工作流步骤，无则为空列表")

    @model_validator(mode="after")
    def sort_workflow_steps(self):
        """保证步骤按 step_order 输出"""
        if self.workflow_steps:
            self.workflow_steps = sorted(self.workflow_steps, key=lambda x: x.step_order)
        return self

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        """将状态值转换为小写"""
        if isinstance(v, str):
            return v.lower()
        if hasattr(v, "value"):
            return v.value.lower()
        return str(v).lower()

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """Ticket 列表响应模型"""

    tickets: List[TicketResponse]
    total: int
    limit: int
    offset: int
