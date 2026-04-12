import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .api import api_router
from .config import settings
from .database import check_db_health, engine
from .limiter import limiter


# ---------- 结构化 JSON 日志 ----------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if record.exc_info and record.exc_info[0]:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO if settings.ENVIRONMENT != "development" else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动与关闭：释放数据库连接池"""
    logger.info("Starting %s (env=%s)", settings.PROJECT_NAME, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)
    engine.dispose()


# ---------- FastAPI 实例 ----------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.2.0",
    description="Ticket Management System API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------- 可信 Host（生产请在 .env 配置 TRUSTED_HOSTS）----------
trusted = settings.TRUSTED_HOSTS
if trusted:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# ---------- 请求日志 + X-Request-ID + 安全响应头 ----------
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    response.headers["X-Request-ID"] = request_id
    if settings.ENABLE_SECURITY_HEADERS:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

    log_record = logging.LogRecord(
        name="access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)",
        args=(),
        exc_info=None,
    )
    log_record.request_id = request_id
    logger.handle(log_record)

    return response


# ---------- 全局异常处理 ----------
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("数据库错误: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "数据库操作失败，请稍后重试"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("未处理异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务内部错误"},
    )


# ---------- 路由 ----------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ---------- 健康检查（含 DB） ----------
@app.get("/health")
async def health_check():
    # 同步 engine.connect() 若在 async 路由内直接调用会阻塞整个事件循环，导致其它请求（含登录）长时间无响应
    db_ok = await run_in_threadpool(check_db_health)
    status_val = "ok" if db_ok else "degraded"
    code = 200 if db_ok else 503
    return JSONResponse(
        status_code=code,
        content={
            "status": status_val,
            "service": settings.PROJECT_NAME,
            "database": "connected" if db_ok else "unreachable",
        },
    )


@app.get("/")
async def root():
    return {
        "message": "Welcome to EQ Management Platform API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
