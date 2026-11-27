"""Camada de routers (controladores HTTP e definição de rotas)."""

from app.routers.announcements import router as announcements_router
from app.routers.assessments import router as assessments_router
from app.routers.auth import router as auth_router
from app.routers.classes import router as classes_router
from app.routers.competencies import router as competencies_router
from app.routers.courses import router as courses_router
from app.routers.dashboard import router as dashboard_router
from app.routers.enrollments import router as enrollments_router
from app.routers.health import router as health_router
from app.routers.learning_modules import router as learning_modules_router
from app.routers.lessons import router as lessons_router
from app.routers.practical_tasks import router as practical_tasks_router
from app.routers.self_assessments import router as self_assessments_router
from app.routers.subjects import router as subjects_router
from app.routers.teacher_assignments import router as teacher_assignments_router

__all__ = [
    "announcements_router",
    "assessments_router",
    "auth_router",
    "classes_router",
    "competencies_router",
    "courses_router",
    "dashboard_router",
    "enrollments_router",
    "health_router",
    "learning_modules_router",
    "lessons_router",
    "practical_tasks_router",
    "self_assessments_router",
    "subjects_router",
    "teacher_assignments_router",
]
