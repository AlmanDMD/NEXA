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
from app.repositories.enrollment_repository import (
    EnrollmentRepository,
    EnrollmentRepositoryDep,
    get_enrollment_repository,
)
from app.repositories.learning_module_repository import (
    LearningModuleRepository,
    LearningModuleRepositoryDep,
    get_learning_module_repository,
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
    "ClassLessonRepository",
    "ClassLessonRepositoryDep",
    "CompetencyRepository",
    "CompetencyRepositoryDep",
    "CourseRepository",
    "CourseRepositoryDep",
    "DashboardRepository",
    "DashboardRepositoryDep",
    "EnrollmentRepository",
    "EnrollmentRepositoryDep",
    "LearningModuleRepository",
    "LearningModuleRepositoryDep",
    "PracticalTaskRepository",
    "PracticalTaskRepositoryDep",
    "RiskEngineRepository",
    "RiskEngineRepositoryDep",
    "SubjectRepository",
    "SubjectRepositoryDep",
    "TeacherAssignmentRepository",
    "TeacherAssignmentRepositoryDep",
    "get_academic_assessment_repository",
    "get_academic_class_repository",
    "get_audit_repository",
    "get_auth_repository",
    "get_class_lesson_repository",
    "get_competency_repository",
    "get_course_repository",
    "get_dashboard_repository",
    "get_enrollment_repository",
    "get_learning_module_repository",
    "get_practical_task_repository",
    "get_risk_engine_repository",
    "get_subject_repository",
    "get_teacher_assignment_repository",
]
