"""认证相关请求/响应模型"""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """登录返回的访问令牌与刷新令牌"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """使用 refresh_token 换取新的 access_token"""

    refresh_token: str = Field(..., min_length=10)


class PasswordChange(BaseModel):
    """修改密码"""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserPublic(BaseModel):
    """对外可见的用户信息"""

    id: int
    username: str

    model_config = {"from_attributes": True}


class UserRegister(BaseModel):
    """注册请求体（密码至少 8 位，与生产常见策略一致）"""

    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
