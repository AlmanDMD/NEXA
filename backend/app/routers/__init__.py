"""Camada de routers (controladores HTTP e definição de rotas)."""

from app.routers.auth import router as auth_router
from app.routers.classes import router as classes_router
from app.routers.courses import router as courses_router
from app.routers.health import router as health_router
from app.routers.subjects import router as subjects_router

__all__ = [
    "auth_router",
    "classes_router",
    "courses_router",
    "health_router",
    "subjects_router",
]
