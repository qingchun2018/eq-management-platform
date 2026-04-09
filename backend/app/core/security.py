"""密码哈希与 JWT 签发/校验（access / refresh）"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from ..config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与存储的哈希是否一致"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希（bcrypt）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(*, subject: str, expires_delta: timedelta | None = None) -> str:
    """签发访问令牌 JWT，sub 为用户名"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": subject, "exp": expire, "typ": "access"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(*, subject: str) -> str:
    """签发刷新令牌 JWT（使用独立 secret）"""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": subject, "exp": expire, "typ": "refresh"}
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """解析 access JWT，成功返回用户名（sub）"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("typ") == "refresh":
            return None
        sub = payload.get("sub")
        if isinstance(sub, str):
            return sub
        return None
    except JWTError:
        return None


def decode_refresh_token(token: str) -> str | None:
    """解析 refresh JWT（使用独立 secret），成功返回用户名（sub）"""
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("typ") != "refresh":
            return None
        sub = payload.get("sub")
        if isinstance(sub, str):
            return sub
        return None
    except JWTError:
        return None
