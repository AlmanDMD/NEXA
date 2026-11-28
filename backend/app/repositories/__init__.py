"""Camada de repositories (acesso e persistência de dados)."""

from app.repositories.academic_assessment_repository import (
    AcademicAssessmentRepository,
    AcademicAssessmentRepositoryDep,
    get_academic_assessment_repository,
)
from app.repositories.academic_class_repository import (
    AcademicClassRepository,
    AcademicClassRepositoryDep,
    get_academic_class_repository,
)
from app.repositories.audit_repository import (
    AuditRepository,
    AuditRepositoryDep,
    get_audit_repository,
)
from app.repositories.auth_repository import (
    AuthRepository,
    AuthRepositoryDep,
    get_auth_repository,
)
from app.repositories.class_announcement_repository import (
    ClassAnnouncementRepository,
    ClassAnnouncementRepositoryDep,
    get_class_announcement_repository,
)
from app.repositories.class_lesson_repository import (
    ClassLessonRepository,
    ClassLessonRepositoryDep,
    get_class_lesson_repository,
)
from app.repositories.competency_repository import (
    CompetencyRepository,
    CompetencyRepositoryDep,
    get_competency_repository,
)
from app.repositories.course_repository import (
    CourseRepository,
    CourseRepositoryDep,
    get_course_repository,
)
from app.repositories.dashboard_repository import (
    DashboardRepository,
    DashboardRepositoryDep,
    get_dashboard_repository,
)
from app.repositories.diagnostic_repository import (
    DiagnosticRepository,
    DiagnosticRepositoryDep,
    get_diagnostic_repository,
)
from app.repositories.enrollment_repository import (
    EnrollmentRepository,
    EnrollmentRepositoryDep,
    get_enrollment_repository,
)
from app.repositories.gamification_repository import (
    DEFAULT_SENAI_BADGES_CATALOG,
    GamificationRepository,
    GamificationRepositoryDep,
    get_gamification_repository,
)
from app.repositories.help_request_repository import (
    HelpRequestRepository,
    HelpRequestRepositoryDep,
    get_help_request_repository,
)
from app.repositories.learning_module_repository import (
    LearningModuleRepository,
    LearningModuleRepositoryDep,
    get_learning_module_repository,
)
from app.repositories.pedagogical_note_repository import (
    PedagogicalNoteRepository,
    PedagogicalNoteRepositoryDep,
    get_pedagogical_note_repository,
)
from app.repositories.practical_task_repository import (
    PracticalTaskRepository,
    PracticalTaskRepositoryDep,
    get_practical_task_repository,
)
from app.repositories.risk_engine_repository import (
    RiskEngineRepository,
    RiskEngineRepositoryDep,
    get_risk_engine_repository,
)
from app.repositories.self_assessment_repository import (
    SelfAssessmentRepository,
    SelfAssessmentRepositoryDep,
    get_self_assessment_repository,
)
from app.repositories.subject_repository import (
    SubjectRepository,
    SubjectRepositoryDep,
    get_subject_repository,
)
from app.repositories.teacher_assignment_repository import (
    TeacherAssignmentRepository,
    TeacherAssignmentRepositoryDep,
    get_teacher_assignment_repository,
)

__all__ = [
    "AcademicAssessmentRepository",
    "AcademicAssessmentRepositoryDep",
    "AcademicClassRepository",
    "AcademicClassRepositoryDep",
    "AuditRepository",
    "AuditRepositoryDep",
    "AuthRepository",
    "AuthRepositoryDep",
    "ClassAnnouncementRepository",
    "ClassAnnouncementRepositoryDep",
    "ClassLessonRepository",
    "ClassLessonRepositoryDep",
    "CompetencyRepository",
    "CompetencyRepositoryDep",
    "CourseRepository",
    "CourseRepositoryDep",
    "DashboardRepository",
    "DashboardRepositoryDep",
    "DEFAULT_SENAI_BADGES_CATALOG",
    "DiagnosticRepository",
    "DiagnosticRepositoryDep",
    "EnrollmentRepository",
    "EnrollmentRepositoryDep",
    "GamificationRepository",
    "GamificationRepositoryDep",
    "HelpRequestRepository",
    "HelpRequestRepositoryDep",
    "LearningModuleRepository",
    "LearningModuleRepositoryDep",
    "PedagogicalNoteRepository",
    "PedagogicalNoteRepositoryDep",
    "PracticalTaskRepository",
    "PracticalTaskRepositoryDep",
    "RiskEngineRepository",
    "RiskEngineRepositoryDep",
    "SelfAssessmentRepository",
    "SelfAssessmentRepositoryDep",
    "SubjectRepository",
    "SubjectRepositoryDep",
    "TeacherAssignmentRepository",
    "TeacherAssignmentRepositoryDep",
    "get_academic_assessment_repository",
    "get_academic_class_repository",
    "get_audit_repository",
    "get_auth_repository",
    "get_class_announcement_repository",
    "get_class_lesson_repository",
    "get_competency_repository",
    "get_course_repository",
    "get_dashboard_repository",
    "get_diagnostic_repository",
    "get_enrollment_repository",
    "get_gamification_repository",
    "get_help_request_repository",
    "get_learning_module_repository",
    "get_pedagogical_note_repository",
    "get_practical_task_repository",
    "get_risk_engine_repository",
    "get_self_assessment_repository",
    "get_subject_repository",
    "get_teacher_assignment_repository",
]
