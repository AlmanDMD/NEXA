"""Serviço de domínio para gestão de Turmas Acadêmicas e Períodos Letivos (BE-012)."""

from typing import Annotated, Final
import unicodedata
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.academic_class import AcademicClass
from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.academic_class_repository import (
    AcademicClassRepository,
    AcademicClassRepositoryDep,
)
from app.repositories.course_repository import CourseRepository, CourseRepositoryDep
from app.schemas.academic_class import (
    AcademicClassCreateSchema,
    AcademicClassListQueryParams,
    AcademicClassPaginatedResponseSchema,
    AcademicClassResponseSchema,
    AcademicClassStatusUpdateSchema,
    ClassEnrolledStudentItemSchema,
    ClassStudentsListQueryParams,
    ClassStudentsResponseSchema,
    CourseSummarySchema,
)
from app.schemas.enums import ClassStatus, UserRole

CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
CLASS_COURSE_NOT_FOUND_MESSAGE: Final[str] = "Curso técnico não encontrado."
CLASS_INACTIVE_COURSE_MESSAGE: Final[str] = (
    "Não é possível criar turma para um curso técnico inativo."
)
CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE: Final[str] = (
    "Não é possível ativar uma turma vinculada a um curso técnico inativo."
)
CLASS_CODE_PERIOD_CONFLICT_MESSAGE: Final[str] = (
    "Já existe uma turma cadastrada com este código neste período letivo."
)
CLASS_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado nesta turma."
)
CLASS_REOPEN_FORBIDDEN_MESSAGE: Final[str] = (
    "Apenas administradores podem reabrir uma turma já concluída ou arquivada."
)

_ALLOWED_STATUS_TRANSITIONS: Final[dict[ClassStatus, set[ClassStatus]]] = {
    ClassStatus.PLANNING: {ClassStatus.ACTIVE, ClassStatus.ARCHIVED},
    ClassStatus.ACTIVE: {ClassStatus.COMPLETED, ClassStatus.ARCHIVED},
    ClassStatus.COMPLETED: {ClassStatus.ARCHIVED},
    ClassStatus.ARCHIVED: set(),
}

_REOPEN_TRANSITIONS: Final[set[tuple[ClassStatus, ClassStatus]]] = {
    (ClassStatus.COMPLETED, ClassStatus.ACTIVE),
    (ClassStatus.ARCHIVED, ClassStatus.ACTIVE),
}


class AcademicClassService:
    """Serviço responsável pelas regras de negócio e autorização contextual de turmas."""

    def __init__(
        self,
        repository: AcademicClassRepository,
        course_repository: CourseRepository,
    ) -> None:
        self._repository = repository
        self._course_repository = course_repository

    @staticmethod
    def _to_response(
        academic_class: AcademicClass,
        *,
        enrolled_students_count: int,
    ) -> AcademicClassResponseSchema:
        """Converte o modelo ORM AcademicClass no schema detalhado com ocupação de vagas."""
        safe_enrolled = max(0, enrolled_students_count)
        available_slots = max(0, academic_class.max_students - safe_enrolled)
        return AcademicClassResponseSchema(
            id=academic_class.id,
            course_id=academic_class.course_id,
            code=academic_class.code,
            period=academic_class.period,
            shift=academic_class.shift,
            max_students=academic_class.max_students,
            enrolled_students_count=safe_enrolled,
            available_slots=available_slots,
            status=academic_class.status,
            start_date=academic_class.start_date,
            end_date=academic_class.end_date,
            course=CourseSummarySchema.model_validate(academic_class.course),
            created_at=academic_class.created_at,
            updated_at=academic_class.updated_at,
        )

    @staticmethod
    def _student_sort_key(item: ClassEnrolledStudentItemSchema) -> tuple[str, str, str]:
        """Gera chave determinística para ordenação alfabética ignorando acentos e caixa."""
        normalized_ascii = "".join(
            ch
            for ch in unicodedata.normalize("NFKD", item.full_name)
            if not unicodedata.combining(ch)
        ).casefold()
        return (normalized_ascii, item.full_name.casefold(), item.email.casefold())

    @staticmethod
    def _to_student_item(enrollment: Enrollment) -> ClassEnrolledStudentItemSchema:
        """Converte uma matrícula ORM (com student e profile carregados) em item da pauta."""
        student = enrollment.student
        profile = student.profile
        raw_full_name = profile.full_name.strip() if profile and profile.full_name else ""
        full_name = raw_full_name or student.email
        return ClassEnrolledStudentItemSchema(
            id=student.id,
            student_id=student.id,
            enrollment_id=enrollment.id,
            full_name=full_name,
            email=student.email,
            registration_number=profile.registration_number if profile else None,
            enrollment_date=enrollment.enrollment_date,
            status=enrollment.status,
            attendance_rate=enrollment.attendance_rate,
            final_grade=enrollment.final_grade,
        )

    def list_classes(
        self,
        params: AcademicClassListQueryParams,
        *,
        current_user: User,
    ) -> AcademicClassPaginatedResponseSchema:
        """Lista turmas paginadas com filtros e escopo contextual para docentes."""
        teacher_id = current_user.id if current_user.role == UserRole.TEACHER else None
        items, total = self._repository.list_classes(
            page=params.page,
            limit=params.limit,
            course_id=params.course_id,
            period=params.period,
            shift=params.shift,
            status=params.status,
            search=params.search,
            teacher_id=teacher_id,
        )
        enrolled_counts = self._repository.count_active_enrollments_by_class_ids(
            [item.id for item in items]
        )
        return AcademicClassPaginatedResponseSchema(
            data=[
                self._to_response(
                    item,
                    enrolled_students_count=enrolled_counts.get(item.id, 0),
                )
                for item in items
            ],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def get_class(
        self,
        class_id: UUID,
        *,
        current_user: User,
    ) -> AcademicClassResponseSchema:
        """Obtém os detalhes da turma com curso vinculado e contagem de alunos matriculados."""
        academic_class = self._repository.get_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=CLASS_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER and not self._repository.is_teacher_assigned_to_class(
            teacher_id=current_user.id,
            class_id=academic_class.id,
        ):
            raise ForbiddenException(message=CLASS_TEACHER_FORBIDDEN_MESSAGE)

        enrolled_count = self._repository.count_active_enrollments(academic_class.id)
        return self._to_response(
            academic_class,
            enrolled_students_count=enrolled_count,
        )

    def list_class_students(
        self,
        class_id: UUID,
        *,
        params: ClassStudentsListQueryParams | None = None,
        current_user: User,
    ) -> ClassStudentsResponseSchema:
        """Lista os alunos matriculados na turma em ordem alfabética com metadados da turma."""
        academic_class = self._repository.get_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=CLASS_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER and not self._repository.is_teacher_assigned_to_class(
            teacher_id=current_user.id,
            class_id=academic_class.id,
        ):
            raise ForbiddenException(message=CLASS_TEACHER_FORBIDDEN_MESSAGE)

        enrolled_count = self._repository.count_active_enrollments(academic_class.id)
        enrollments = self._repository.list_enrolled_students(
            academic_class.id,
            status=params.status if params else None,
            search=params.search if params else None,
        )
        student_items = sorted(
            (self._to_student_item(enrollment) for enrollment in enrollments),
            key=self._student_sort_key,
        )
        return ClassStudentsResponseSchema(
            academic_class=self._to_response(
                academic_class,
                enrolled_students_count=enrolled_count,
            ),
            total=len(student_items),
            data=student_items,
        )

    def create_class(self, payload: AcademicClassCreateSchema) -> AcademicClassResponseSchema:
        """Cria uma nova turma vinculada a curso ativo garantindo unicidade de (code, period)."""
        course = self._course_repository.get_by_id(payload.course_id)
        if course is None:
            raise NotFoundException(message=CLASS_COURSE_NOT_FOUND_MESSAGE)

        if not course.is_active:
            raise UnprocessableEntityException(message=CLASS_INACTIVE_COURSE_MESSAGE)

        existing = self._repository.get_by_code_and_period(payload.code, payload.period)
        if existing is not None:
            raise ConflictException(message=CLASS_CODE_PERIOD_CONFLICT_MESSAGE)

        created = self._repository.create(
            course_id=payload.course_id,
            code=payload.code,
            period=payload.period,
            shift=payload.shift,
            max_students=payload.max_students,
            status=payload.status,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        logger.bind(
            class_id=str(created.id),
            course_id=str(created.course_id),
            code=created.code,
            period=created.period,
            shift=created.shift.value,
            status=created.status.value,
        ).info("Nova turma acadêmica cadastrada com sucesso.")
        return self._to_response(created, enrolled_students_count=0)

    def update_class_status(
        self,
        class_id: UUID,
        payload: AcademicClassStatusUpdateSchema,
        *,
        current_user: User,
    ) -> AcademicClassResponseSchema:
        """Atualiza o status da turma respeitando regras de transição e reabertura por ADMIN."""
        academic_class = self._repository.get_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=CLASS_NOT_FOUND_MESSAGE)

        if academic_class.status == payload.status:
            enrolled_count = self._repository.count_active_enrollments(academic_class.id)
            return self._to_response(
                academic_class,
                enrolled_students_count=enrolled_count,
            )

        transition = (academic_class.status, payload.status)
        if transition in _REOPEN_TRANSITIONS:
            if current_user.role != UserRole.ADMIN:
                raise ForbiddenException(message=CLASS_REOPEN_FORBIDDEN_MESSAGE)
        elif payload.status not in _ALLOWED_STATUS_TRANSITIONS[academic_class.status]:
            raise UnprocessableEntityException(
                message=(
                    f"Transição de status inválida de '{academic_class.status.value}' "
                    f"para '{payload.status.value}'."
                ),
                error="INVALID_STATUS_TRANSITION",
            )

        if payload.status == ClassStatus.ACTIVE and not academic_class.course.is_active:
            raise UnprocessableEntityException(message=CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE)

        previous_status = academic_class.status
        updated = self._repository.update_status(academic_class, status=payload.status)
        enrolled_count = self._repository.count_active_enrollments(updated.id)
        logger.bind(
            class_id=str(updated.id),
            code=updated.code,
            period=updated.period,
            previous_status=previous_status.value,
            new_status=updated.status.value,
            actor_id=str(current_user.id),
        ).info("Status da turma acadêmica atualizado com sucesso.")
        return self._to_response(
            updated,
            enrolled_students_count=enrolled_count,
        )


def get_academic_class_service(
    repository: AcademicClassRepositoryDep,
    course_repository: CourseRepositoryDep,
) -> AcademicClassService:
    """Provedor de injeção de dependência para AcademicClassService."""
    return AcademicClassService(
        repository=repository,
        course_repository=course_repository,
    )


AcademicClassServiceDep = Annotated[
    AcademicClassService,
    Depends(get_academic_class_service),
]

__all__ = [
    "AcademicClassService",
    "AcademicClassServiceDep",
    "CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE",
    "CLASS_CODE_PERIOD_CONFLICT_MESSAGE",
    "CLASS_COURSE_NOT_FOUND_MESSAGE",
    "CLASS_INACTIVE_COURSE_MESSAGE",
    "CLASS_NOT_FOUND_MESSAGE",
    "CLASS_REOPEN_FORBIDDEN_MESSAGE",
    "CLASS_TEACHER_FORBIDDEN_MESSAGE",
    "get_academic_class_service",
]
