"""Camada de repositories (acesso e persistência de dados)."""

from app.repositories.academic_class_repository import (
    AcademicClassRepository,
    AcademicClassRepositoryDep,
    get_academic_class_repository,
)
from app.repositories.auth_repository import (
    AuthRepository,
    AuthRepositoryDep,
    get_auth_repository,
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
from app.repositories.subject_repository import (
    SubjectRepository,
    SubjectRepositoryDep,
    get_subject_repository,
)

__all__ = [
    "AcademicClassRepository",
    "AcademicClassRepositoryDep",
    "AuthRepository",
    "AuthRepositoryDep",
    "CompetencyRepository",
    "CompetencyRepositoryDep",
    "CourseRepository",
    "CourseRepositoryDep",
    "EnrollmentRepository",
    "EnrollmentRepositoryDep",
    "LearningModuleRepository",
    "LearningModuleRepositoryDep",
    "SubjectRepository",
    "SubjectRepositoryDep",
    "get_academic_class_repository",
    "get_auth_repository",
    "get_competency_repository",
    "get_course_repository",
    "get_enrollment_repository",
    "get_learning_module_repository",
    "get_subject_repository",
]
