"""API routes"""

from fastapi import APIRouter

from .audit import router as audit_router
from .auth import router as auth_router
from .projects import router as projects_router
from .tags import router as tags_router
from .tickets import router as tickets_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(tickets_router)
api_router.include_router(tags_router)
api_router.include_router(audit_router)

__all__ = ["api_router"]
