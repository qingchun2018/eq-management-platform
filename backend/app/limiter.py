"""API 限流（slowapi），按客户端 IP。"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# default_limits 为空，仅在路由上使用 @limiter.limit
limiter = Limiter(key_func=get_remote_address, default_limits=[])
