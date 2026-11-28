"""Camada de models (entidades de domínio / persistência SQLAlchemy 2.0)."""

from app.models.academic_alert import (
    AcademicAlert,
    VW_STUDENT_360_PERFORMANCE_CREATE_SQL,
    VW_STUDENT_360_PERFORMANCE_DROP_SQL,
    VW_STUDENT_360_PERFORMANCE_NAME,
    vw_student_360_performance_table,
)
from app.models.academic_assessment import AcademicAssessment, StudentGrade
from app.models.academic_class import AcademicClass
from app.models.audit_log import AuditLog
from app.models.auth_session import AuthSession
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.class_announcement import ClassAnnouncement
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
from app.models.gamification import GamificationBadge, StudentAchievement
from app.models.help_request import ChatMessage, HelpRequest
from app.models.learning_module import LearningModule
from app.models.module_competency import ModuleCompetency
from app.models.pedagogical_note import PedagogicalNote
from app.models.practical_task import (
    PracticalTask,
    SkillEvidence,
    SubmissionEvaluation,
    TaskCriterion,
    TaskSubmission,
)
from app.models.self_assessment import (
    ExplainableDiagnostic,
    SelfAssessmentForm,
    StudentSelfAssessment,
    VW_SELF_EVAL_DISCREPANCY_CREATE_SQL,
    VW_SELF_EVAL_DISCREPANCY_DROP_SQL,
    VW_SELF_EVAL_DISCREPANCY_NAME,
    vw_self_eval_discrepancy_table,
)
from app.models.student_milestone_history import StudentMilestoneHistory
from app.models.subject import Subject
from app.models.teacher_assignment import TeacherAssignment
from app.models.user import User, UserProfile

__all__ = [
    "AcademicAlert",
    "AcademicAssessment",
    "AcademicClass",
    "AttendanceRecord",
    "AuditLog",
    "AuthSession",
    "Base",
    "ChatMessage",
    "ClassAnnouncement",
    "ClassLesson",
    "Competency",
    "Course",
    "Enrollment",
    "ExplainableDiagnostic",
    "GamificationBadge",
    "HelpRequest",
    "LearningModule",
    "ModuleCompetency",
    "PedagogicalNote",
    "PracticalTask",
    "SelfAssessmentForm",
    "SkillEvidence",
    "StudentAchievement",
    "StudentGrade",
    "StudentMilestoneHistory",
    "StudentSelfAssessment",
    "Subject",
    "SubmissionEvaluation",
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
    "VW_SELF_EVAL_DISCREPANCY_CREATE_SQL",
    "VW_SELF_EVAL_DISCREPANCY_DROP_SQL",
    "VW_SELF_EVAL_DISCREPANCY_NAME",
    "VW_STUDENT_360_PERFORMANCE_CREATE_SQL",
    "VW_STUDENT_360_PERFORMANCE_DROP_SQL",
    "VW_STUDENT_360_PERFORMANCE_NAME",
    "vw_module_attendance_risk_table",
    "vw_self_eval_discrepancy_table",
    "vw_student_360_performance_table",
]
