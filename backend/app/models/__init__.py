"""Camada de models (entidades de domínio / persistência SQLAlchemy 2.0)."""

from app.models.academic_class import AcademicClass
from app.models.audit_log import AuditLog
from app.models.auth_session import AuthSession
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.class_lesson import (
    AttendanceRecord,
    ClassLesson,
    VW_MODULE_ATTENDANCE_RISK_CREATE_SQL,
    VW_MODULE_ATTENDANCE_RISK_DROP_SQL,
    VW_MODULE_ATTENDANCE_RISK_NAME,
    vw_module_attendance_risk_table,
)
from app.models.competency import Competency
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.learning_module import LearningModule
from app.models.module_competency import ModuleCompetency
from app.models.practical_task import PracticalTask, TaskCriterion, TaskSubmission
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User, UserProfile

__all__ = [
    "AcademicClass",
    "AttendanceRecord",
    "AuditLog",
    "AuthSession",
    "Base",
    "ClassLesson",
    "Competency",
    "Course",
    "Enrollment",
    "LearningModule",
    "ModuleCompetency",
    "PracticalTask",
    "Subject",
    "TaskCriterion",
    "TaskSubmission",
    "TeacherAssignment",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "UserProfile",
    "VW_MODULE_ATTENDANCE_RISK_CREATE_SQL",
    "VW_MODULE_ATTENDANCE_RISK_DROP_SQL",
    "VW_MODULE_ATTENDANCE_RISK_NAME",
    "vw_module_attendance_risk_table",
]
