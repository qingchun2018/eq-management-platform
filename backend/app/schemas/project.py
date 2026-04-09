"""小组、项目与成员"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .auth import UserPublic


class TeamBrief(BaseModel):
    """小组摘要"""

    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProjectBrief(BaseModel):
    """项目摘要（含当前用户在该项目下的有效角色字符串）"""

    id: int
    team_id: int
    name: str
    description: Optional[str] = None
    my_role: str = Field(description="PROJECT_ADMIN / EDITOR / VIEWER")

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    """在本小组下创建项目（仅组长）"""

    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


class ProjectUpdate(BaseModel):
    """编辑项目名称或描述"""

    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=2000)


class ProjectMemberCreate(BaseModel):
    """向项目添加成员"""

    user_id: int
    role: str = Field(..., description="PROJECT_ADMIN / EDITOR / VIEWER")


class ProjectMemberItem(BaseModel):
    """项目成员项"""

    user: UserPublic
    role: str

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    """登录后前端用于展示权限与项目切换"""

    id: int
    username: str
    team: Optional[TeamBrief] = None
    team_role: Optional[str] = None
    projects: List[ProjectBrief] = Field(default_factory=list)
