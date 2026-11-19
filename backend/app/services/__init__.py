"""Camada de services (regras de negócio da aplicação)."""

from app.services.academic_class_service import (
    AcademicClassService,
    AcademicClassServiceDep,
    CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE,
    CLASS_CODE_PERIOD_CONFLICT_MESSAGE,
    CLASS_COURSE_NOT_FOUND_MESSAGE,
    CLASS_INACTIVE_COURSE_MESSAGE,
    CLASS_NOT_FOUND_MESSAGE,
    CLASS_REOPEN_FORBIDDEN_MESSAGE,
    CLASS_TEACHER_FORBIDDEN_MESSAGE,
    get_academic_class_service,
)
from app.services.auth_service import (
    AuthService,
    AuthServiceDep,
    INVALID_CREDENTIALS_MESSAGE,
    LOGOUT_SUCCESS_MESSAGE,
    REFRESH_TOKEN_EXPIRED_MESSAGE,
    REFRESH_TOKEN_INVALID_MESSAGE,
    REFRESH_TOKEN_MISSING_MESSAGE,
    REFRESH_TOKEN_REVOKED_REUSE_MESSAGE,
    get_auth_service,
)
from app.services.course_service import (
    COURSE_CODE_CONFLICT_MESSAGE,
    COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE,
    COURSE_NOT_FOUND_MESSAGE,
    CourseService,
    CourseServiceDep,
    get_course_service,
)
from app.services.health_service import (
    HealthService,
    HealthServiceDep,
    get_health_service,
)

__all__ = [
    "AcademicClassService",
    "AcademicClassServiceDep",
    "AuthService",
    "AuthServiceDep",
    "CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE",
    "CLASS_CODE_PERIOD_CONFLICT_MESSAGE",
    "CLASS_COURSE_NOT_FOUND_MESSAGE",
    "CLASS_INACTIVE_COURSE_MESSAGE",
    "CLASS_NOT_FOUND_MESSAGE",
    "CLASS_REOPEN_FORBIDDEN_MESSAGE",
    "CLASS_TEACHER_FORBIDDEN_MESSAGE",
    "COURSE_CODE_CONFLICT_MESSAGE",
    "COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE",
    "COURSE_NOT_FOUND_MESSAGE",
    "CourseService",
    "CourseServiceDep",
    "HealthService",
    "HealthServiceDep",
    "INVALID_CREDENTIALS_MESSAGE",
    "LOGOUT_SUCCESS_MESSAGE",
    "REFRESH_TOKEN_EXPIRED_MESSAGE",
    "REFRESH_TOKEN_INVALID_MESSAGE",
    "REFRESH_TOKEN_MISSING_MESSAGE",
    "REFRESH_TOKEN_REVOKED_REUSE_MESSAGE",
    "get_academic_class_service",
    "get_auth_service",
    "get_course_service",
    "get_health_service",
]
