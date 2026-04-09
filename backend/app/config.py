from typing import Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/eq_management"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "EQ 管理平台"

    # CORS - 使用字符串字段，然后在验证器中解析（须同时包含 localhost 与 127.0.0.1，否则用 IP 打开前端会跨域失败）
    ALLOWED_ORIGINS_STR: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
        description="Allowed CORS origins (comma-separated)",
    )

    # Environment
    ENVIRONMENT: str = "development"

    # JWT 认证（生产环境务必通过环境变量覆盖）
    JWT_SECRET_KEY: str = "dev-only-change-me-use-openssl-rand-hex-32"
    JWT_REFRESH_SECRET_KEY: str = "dev-only-refresh-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DB 连接池
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # 是否允许自助注册（内网可临时开启创建首个账号后关闭）
    AUTH_ALLOW_REGISTER: bool = False

    # 安全响应头（非 HTTPS 场景不设置 HSTS，由网关补全）
    ENABLE_SECURITY_HEADERS: bool = True

    # 生产环境建议设置，如 api.example.com,localhost；空表示不启用 TrustedHost 校验
    TRUSTED_HOSTS_STR: str = Field(default="", alias="TRUSTED_HOSTS")

    # slowapi 限流（格式如 15/minute、5/second），开发环境可在 .env 放宽
    RATE_LIMIT_AUTH_LOGIN: str = "20/minute"
    RATE_LIMIT_AUTH_REGISTER: str = "8/minute"
    RATE_LIMIT_AUTH_REFRESH: str = "60/minute"
    RATE_LIMIT_AUTH_CHANGE_PASSWORD: str = "15/minute"

    @field_validator("ALLOWED_ORIGINS_STR", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> Any:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return v
        return str(v)

    @property
    def TRUSTED_HOSTS(self) -> List[str] | None:
        """非空时启用 TrustedHostMiddleware"""
        s = self.TRUSTED_HOSTS_STR.strip() if isinstance(self.TRUSTED_HOSTS_STR, str) else ""
        if not s:
            return None
        return [h.strip() for h in s.split(",") if h.strip()]

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """解析 ALLOWED_ORIGINS_STR 为列表"""
        if isinstance(self.ALLOWED_ORIGINS_STR, list):
            return self.ALLOWED_ORIGINS_STR
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_STR.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """供 SQLAlchemy 使用的 URL：无驱动前缀时改用 psycopg v3，避免 Windows 中文系统下 psycopg2 解析 libpq 报错。"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url


settings = Settings()
