"""Serviço de domínio para Diário de Classe e Registro de Aulas Ministradas (BE-021)."""

from decimal import Decimal
from typing import Annotated, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
)
from app.core.logging import logger
from app.models.class_lesson import ClassLesson
from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.class_lesson_repository import (
    ClassLessonRepository,
    ClassLessonRepositoryDep,
)
from app.schemas.class_lesson import (
    BatchAttendanceRequestSchema,
    BatchAttendanceResponseSchema,
    ClassLessonCreateSchema,
    ClassLessonListQueryParams,
    ClassLessonPaginatedResponseSchema,
    ClassLessonResponseSchema,
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
    LessonTeacherSummarySchema,
    UpdatedEnrollmentAttendanceSchema,
)
from app.schemas.enums import AttendanceStatus, ClassStatus, EnrollmentStatus, RiskLevel, UserRole

LESSON_NOT_FOUND_MESSAGE: Final[str] = "Aula não encontrada no diário de classe."
ATTENDANCE_STUDENT_NOT_ENROLLED_MESSAGE: Final[str] = (
    "Estudante informado na chamada não está matriculado na turma desta aula."
)
ATTENDANCE_INACTIVE_ENROLLMENT_MESSAGE: Final[str] = (
    "Não é possível registrar frequência para matrícula inativa ou trancada (DROPPED)."
)
ATTENDANCE_ABSENT_HOURS_EXCEED_WORKLOAD_MESSAGE: Final[str] = (
    "A quantidade de horas ausentes (absent_hours) não pode ultrapassar a carga horária da aula."
)
ATTENDANCE_PRESENT_WITH_ABSENT_HOURS_MESSAGE: Final[str] = (
    "Alunos com status PRESENT não podem ter horas de falta (absent_hours > 0)."
)
ATTENDANCE_CRITICAL_THRESHOLD: Final[Decimal] = Decimal("78.00")
ATTENDANCE_FAIL_THRESHOLD: Final[Decimal] = Decimal("75.00")
LESSON_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
LESSON_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina técnica não encontrada."
LESSON_MODULE_NOT_FOUND_MESSAGE: Final[str] = "Módulo de aprendizagem prática não encontrado."
LESSON_TEACHER_NOT_FOUND_MESSAGE: Final[str] = "Docente não encontrado."
LESSON_INVALID_TEACHER_ROLE_MESSAGE: Final[str] = (
    "O usuário indicado como docente não possui perfil TEACHER cadastrado."
)
LESSON_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa para esta turma e disciplina."
)
LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não está alocado nesta turma."
)
LESSON_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível registrar aula em uma turma que não está ativa."
)
LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "A disciplina informada não pertence ao curso técnico da turma."
)
LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence à disciplina selecionada."
)


class ClassLessonService:
    """Serviço responsável pelo registro diário de aulas, RBAC docente e chamada inicial."""

    def __init__(self, repository: ClassLessonRepository) -> None:
        self._repository = repository

    @staticmethod
    def _to_response(lesson: ClassLesson) -> ClassLessonResponseSchema:
        """Converte ClassLesson ORM no schema detalhado com contagem de chamada inicializada."""
        teacher = lesson.teacher
        profile = teacher.profile
        return ClassLessonResponseSchema(
            id=lesson.id,
            class_id=lesson.class_id,
            subject_id=lesson.subject_id,
            module_id=lesson.module_id,
            teacher_id=lesson.teacher_id,
            lesson_date=lesson.lesson_date,
            workload_hours=lesson.workload_hours,
            topic_summary=lesson.topic_summary,
            lab_environment=lesson.lab_environment,
            initialized_attendance_count=len(lesson.attendance_records),
            teacher=LessonTeacherSummarySchema(
                id=teacher.id,
                email=teacher.email,
                full_name=profile.full_name if profile is not None else None,
                registration_number=(
                    profile.registration_number if profile is not None else None
                ),
            ),
            subject=LessonSubjectSummarySchema.model_validate(lesson.subject),
            module=(
                LessonModuleSummarySchema.model_validate(lesson.module)
                if lesson.module is not None
                else None
            ),
            created_at=lesson.created_at,
        )

    def create_lesson(
        self,
        payload: ClassLessonCreateSchema,
        *,
        current_user: User,
    ) -> ClassLessonResponseSchema:
        """Registra aula ministrada validando alocação docente, turma ativa e módulo vinculado."""
        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=LESSON_CLASS_NOT_FOUND_MESSAGE)

        subject = self._repository.get_subject_by_id(payload.subject_id)
        if subject is None:
            raise NotFoundException(message=LESSON_SUBJECT_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER:
            if (
                payload.teacher_id is not None and payload.teacher_id != current_user.id
            ) or not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            ):
                raise ForbiddenException(message=LESSON_TEACHER_FORBIDDEN_MESSAGE)
            resolved_teacher_id = current_user.id
        else:
            if payload.teacher_id is not None:
                assigned_teacher = self._repository.get_user_by_id(payload.teacher_id)
                if assigned_teacher is None:
                    raise NotFoundException(message=LESSON_TEACHER_NOT_FOUND_MESSAGE)
                if assigned_teacher.role != UserRole.TEACHER:
                    raise BadRequestException(message=LESSON_INVALID_TEACHER_ROLE_MESSAGE)
                resolved_teacher_id = assigned_teacher.id
            else:
                resolved_teacher_id = current_user.id

        if academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=LESSON_INACTIVE_CLASS_MESSAGE)

        if subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(message=LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE)

        if payload.module_id is not None:
            module = self._repository.get_module_by_id(payload.module_id)
            if module is None:
                raise NotFoundException(message=LESSON_MODULE_NOT_FOUND_MESSAGE)
            if module.subject_id != subject.id:
                raise UnprocessableEntityException(
                    message=LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE
                )

        created = self._repository.create_lesson_with_initial_attendance(
            class_id=academic_class.id,
            subject_id=subject.id,
            module_id=payload.module_id,
            teacher_id=resolved_teacher_id,
            lesson_date=payload.lesson_date,
            workload_hours=payload.workload_hours,
            topic_summary=payload.topic_summary,
            lab_environment=payload.lab_environment,
        )
        logger.bind(
            lesson_id=str(created.id),
            class_id=str(created.class_id),
            subject_id=str(created.subject_id),
            module_id=str(created.module_id) if created.module_id else None,
            teacher_id=str(created.teacher_id),
            lesson_date=created.lesson_date.isoformat(),
            workload_hours=created.workload_hours,
            initialized_attendance_count=len(created.attendance_records),
        ).info("Aula ministrada registrada com chamada em lote pré-inicializada.")
        return self._to_response(created)

    def list_class_lessons(
        self,
        class_id: UUID,
        params: ClassLessonListQueryParams,
        *,
        current_user: User,
    ) -> ClassLessonPaginatedResponseSchema:
        """Lista aulas do diário de classe de uma turma com filtros e RBAC docente contextual."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=LESSON_CLASS_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
        ):
            raise ForbiddenException(message=LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE)

        items, total = self._repository.list_by_class(
            academic_class.id,
            page=params.page,
            limit=params.limit,
            subject_id=params.subject_id,
            module_id=params.module_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        return ClassLessonPaginatedResponseSchema(
            data=[self._to_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def record_batch_attendance(
        self,
        lesson_id: UUID,
        payload: BatchAttendanceRequestSchema,
        *,
        current_user: User,
    ) -> BatchAttendanceResponseSchema:
        """Executa chamada rápida em lote e recalcula attendance_rate e risco (<78%) no servidor."""
        lesson = self._repository.get_by_id(lesson_id)
        if lesson is None:
            raise NotFoundException(message=LESSON_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=lesson.class_id,
                subject_id=lesson.subject_id,
            )
        ):
            raise ForbiddenException(message=LESSON_TEACHER_FORBIDDEN_MESSAGE)

        enrollments_by_student = self._repository.get_enrollments_by_class(lesson.class_id)
        normalized_items: list[tuple[Enrollment, AttendanceStatus, int, str | None]] = []

        for item in payload.records:
            enrollment = enrollments_by_student.get(item.student_id)
            if enrollment is None:
                raise BadRequestException(message=ATTENDANCE_STUDENT_NOT_ENROLLED_MESSAGE)

            if enrollment.status != EnrollmentStatus.ACTIVE:
                raise BadRequestException(message=ATTENDANCE_INACTIVE_ENROLLMENT_MESSAGE)

            if item.absent_hours is not None and item.absent_hours > lesson.workload_hours:
                raise BadRequestException(
                    message=ATTENDANCE_ABSENT_HOURS_EXCEED_WORKLOAD_MESSAGE
                )

            if item.status == AttendanceStatus.PRESENT:
                if item.absent_hours is not None and item.absent_hours > 0:
                    raise BadRequestException(
                        message=ATTENDANCE_PRESENT_WITH_ABSENT_HOURS_MESSAGE
                    )
                resolved_absent_hours = 0
            elif item.status == AttendanceStatus.ABSENT:
                resolved_absent_hours = (
                    item.absent_hours
                    if (item.absent_hours is not None and item.absent_hours > 0)
                    else lesson.workload_hours
                )
            elif item.status == AttendanceStatus.LATE:
                resolved_absent_hours = (
                    item.absent_hours
                    if (item.absent_hours is not None and item.absent_hours > 0)
                    else min(lesson.workload_hours, 1)
                )
            else:
                resolved_absent_hours = item.absent_hours if item.absent_hours is not None else 0

            normalized_items.append(
                (enrollment, item.status, resolved_absent_hours, item.justification_note)
            )

        rates_by_student = self._repository.upsert_batch_attendance(
            lesson=lesson,
            normalized_items=normalized_items,
        )

        updated_enrollments: list[UpdatedEnrollmentAttendanceSchema] = []
        present_count = 0
        absent_count = 0
        at_risk_students_count = 0

        for enrollment, rec_status, absent_hours, _ in normalized_items:
            rate = rates_by_student[enrollment.student_id]
            is_critical, risk_level = evaluate_attendance_risk_level(rate)
            if rec_status == AttendanceStatus.ABSENT:
                absent_count += 1
            else:
                present_count += 1

            if is_critical:
                at_risk_students_count += 1
                logger.bind(
                    lesson_id=str(lesson.id),
                    class_id=str(lesson.class_id),
                    enrollment_id=str(enrollment.id),
                    student_id=str(enrollment.student_id),
                    attendance_rate=str(rate),
                    risk_level=risk_level.value,
                ).warning(
                    "Motor de risco acionado após chamada: frequência abaixo do limiar preventivo de 78%."
                )

            updated_enrollments.append(
                UpdatedEnrollmentAttendanceSchema(
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    status=rec_status,
                    absent_hours=absent_hours,
                    attendance_rate=rate,
                    is_attendance_critical=is_critical,
                    risk_level=risk_level,
                )
            )

        logger.bind(
            lesson_id=str(lesson.id),
            class_id=str(lesson.class_id),
            actor_id=str(current_user.id),
            total_processed=len(updated_enrollments),
            present_count=present_count,
            absent_count=absent_count,
            at_risk_students_count=at_risk_students_count,
        ).info("Chamada em lote registrada e frequências recalculadas no servidor.")

        return BatchAttendanceResponseSchema(
            lesson_id=lesson.id,
            class_id=lesson.class_id,
            total_processed=len(updated_enrollments),
            present_count=present_count,
            absent_count=absent_count,
            at_risk_students_count=at_risk_students_count,
            updated_enrollments=updated_enrollments,
        )


def evaluate_attendance_risk_level(attendance_rate: Decimal) -> tuple[bool, RiskLevel]:
    """Avalia risco de evasão por frequência segundo limiares preventivos (<78% HIGH, <75% CRITICAL)."""
    if attendance_rate < ATTENDANCE_FAIL_THRESHOLD:
        return True, RiskLevel.CRITICAL
    if attendance_rate < ATTENDANCE_CRITICAL_THRESHOLD:
        return True, RiskLevel.HIGH
    return False, RiskLevel.LOW


def get_class_lesson_service(
    repository: ClassLessonRepositoryDep,
) -> ClassLessonService:
    """Provedor de injeção de dependência para ClassLessonService."""
    return ClassLessonService(repository=repository)


ClassLessonServiceDep = Annotated[
    ClassLessonService,
    Depends(get_class_lesson_service),
]

__all__ = [
    "ATTENDANCE_ABSENT_HOURS_EXCEED_WORKLOAD_MESSAGE",
    "ATTENDANCE_CRITICAL_THRESHOLD",
    "ATTENDANCE_FAIL_THRESHOLD",
    "ATTENDANCE_INACTIVE_ENROLLMENT_MESSAGE",
    "ATTENDANCE_PRESENT_WITH_ABSENT_HOURS_MESSAGE",
    "ATTENDANCE_STUDENT_NOT_ENROLLED_MESSAGE",
    "ClassLessonService",
    "ClassLessonServiceDep",
    "LESSON_CLASS_NOT_FOUND_MESSAGE",
    "LESSON_CLASS_TEACHER_FORBIDDEN_MESSAGE",
    "LESSON_INACTIVE_CLASS_MESSAGE",
    "LESSON_INVALID_TEACHER_ROLE_MESSAGE",
    "LESSON_MODULE_NOT_FOUND_MESSAGE",
    "LESSON_MODULE_SUBJECT_MISMATCH_MESSAGE",
    "LESSON_NOT_FOUND_MESSAGE",
    "LESSON_SUBJECT_COURSE_MISMATCH_MESSAGE",
    "LESSON_SUBJECT_NOT_FOUND_MESSAGE",
    "LESSON_TEACHER_FORBIDDEN_MESSAGE",
    "LESSON_TEACHER_NOT_FOUND_MESSAGE",
    "evaluate_attendance_risk_level",
    "get_class_lesson_service",
]
