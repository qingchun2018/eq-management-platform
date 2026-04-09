from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    """Tag 基础模型"""

    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    color: Optional[str] = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="标签颜色（十六进制格式）"
    )


class TagCreate(TagBase):
    """创建 Tag 请求模型"""

    project_id: int = Field(..., description="所属项目 ID")


class TagUpdate(BaseModel):
    """更新 Tag 请求模型（字段均为可选）"""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagResponse(TagBase):
    """Tag 响应模型"""

    id: int
    created_at: datetime
    ticket_count: Optional[int] = 0

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Tag 列表响应模型"""

    tags: List[TagResponse]
    total: int
