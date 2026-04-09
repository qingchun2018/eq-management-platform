"""审计日志 API 模型"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    id: int
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    project_id: Optional[int] = None
    detail: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: List[AuditLogItem] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 50
