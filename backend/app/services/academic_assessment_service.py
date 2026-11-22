"""Serviço de domínio para Avaliações Formativas e Lançamento de Notas em Lote com Auditoria (BE-027)."""

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
from app.models.academic_assessment import AcademicAssessment, StudentGrade
from app.models.base import _utc_now
from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.academic_assessment_repository import (
    AcademicAssessmentRepository,
    AcademicAssessmentRepositoryDep,
)
from app.repositories.audit_repository import AuditRepository
from app.schemas.academic_assessment import (
    AcademicAssessmentCreateSchema,
    AcademicAssessmentListQueryParams,
    AcademicAssessmentPaginatedResponseSchema,
    AcademicAssessmentResponseSchema,
    BatchStudentGradesRequestSchema,
    BatchStudentGradesResponseSchema,
    StudentGradeItemResponseSchema,
)
from app.schemas.class_lesson import LessonModuleSummarySchema, LessonSubjectSummarySchema
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import ClassStatus, EnrollmentStatus, UserRole
from app.services.audit_service import AuditService, AuditServiceDep

ASSESSMENT_NOT_FOUND_MESSAGE: Final[str] = "Avaliação formativa não encontrada."
ASSESSMENT_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina técnica não encontrada."
ASSESSMENT_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa para esta turma e disciplina."
)
ASSESSMENT_INACTIVE_CLASS_MESSAGE: Final[str] = (
    "Não é possível criar avaliação ou lançar notas em uma turma que não está ativa."
)
ASSESSMENT_INACTIVE_SUBJECT_MESSAGE: Final[str] = (
    "Não é possível criar avaliação em uma disciplina inativa."
)
ASSESSMENT_SUBJECT_COURSE_MISMATCH_MESSAGE: Final[str] = (
    "A disciplina informada não pertence ao curso técnico da turma selecionada."
)
ASSESSMENT_MODULE_SUBJECT_MISMATCH_MESSAGE: Final[str] = (
    "O módulo prático informado não pertence à disciplina selecionada."
)
GRADE_STUDENT_NOT_ENROLLED_MESSAGE: Final[str] = (
    "Estudante informado no lançamento de notas não está matriculado na turma desta avaliação."
)
GRADE_INACTIVE_ENROLLMENT_MESSAGE: Final[str] = (
    "Não é possível lançar nota para matrícula inativa ou trancada (DROPPED)."
)
GRADE_EXCEEDS_MAX_GRADE_MESSAGE: Final[str] = (
    "A nota informada (grade_value ou recovery_grade) não pode ultrapassar a nota máxima (max_grade) da avaliação."
)
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")


def compute_senai_effective_grade(
    grade_value: Decimal,
    recovery_grade: Decimal | None,
) -> tuple[Decimal, bool]:
    """Calcula a nota efetiva considerando a maior nota entre grade_value e recovery_grade (regra SENAI)."""
    normalized_grade = Decimal(grade_value).quantize(_DECIMAL_QUANTIZER)
    if recovery_grade is None:
        return normalized_grade, False
    normalized_recovery = Decimal(recovery_grade).quantize(_DECIMAL_QUANTIZER)
    if normalized_recovery > normalized_grade:
        return normalized_recovery, True
    return normalized_grade, False


class AcademicAssessmentService:
    """Serviço responsável pelo cadastro de avaliações formativas e lançamento de notas em lote com auditoria."""

    def __init__(
        self,
        repository: AcademicAssessmentRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self._repository = repository
        self._audit_service = (
            audit_service
            if audit_service is not None
            else AuditService(repository=AuditRepository(session=repository.session))
        )

    @staticmethod
    def _to_assessment_response(
        assessment: AcademicAssessment,
    ) -> AcademicAssessmentResponseSchema:
        """Converte AcademicAssessment ORM em AcademicAssessmentResponseSchema."""
        return AcademicAssessmentResponseSchema(
            id=assessment.id,
            class_id=assessment.class_id,
            subject_id=assessment.subject_id,
            module_id=assessment.module_id,
            title=assessment.title,
            assessment_type=assessment.assessment_type,
            weight=assessment.weight,
            application_date=assessment.application_date,
            max_grade=assessment.max_grade,
            graded_students_count=len(assessment.grades),
            academic_class=EnrollmentClassSummarySchema.model_validate(
                assessment.academic_class
            ),
            subject=LessonSubjectSummarySchema.model_validate(assessment.subject),
            module=(
                LessonModuleSummarySchema.model_validate(assessment.module)
                if assessment.module is not None
                else None
            ),
            created_at=assessment.created_at,
            updated_at=assessment.updated_at,
        )

    @staticmethod
    def _to_grade_item_response(
        grade: StudentGrade,
        *,
        was_rectified: bool = False,
    ) -> StudentGradeItemResponseSchema:
        """Converte StudentGrade ORM em StudentGradeItemResponseSchema aplicando regra de maior nota SENAI."""
        effective_grade, is_recovery_applied = compute_senai_effective_grade(
            grade.grade_value,
            grade.recovery_grade,
        )
        return StudentGradeItemResponseSchema(
            id=grade.id,
            assessment_id=grade.assessment_id,
            enrollment_id=grade.enrollment_id,
            student_id=grade.student_id,
            recorded_by=grade.recorded_by,
            grade_value=grade.grade_value,
            recovery_grade=grade.recovery_grade,
            effective_grade=effective_grade,
            is_recovery_applied=is_recovery_applied,
            was_rectified=was_rectified,
            comments=grade.comments,
            created_at=grade.created_at,
            updated_at=grade.updated_at,
        )

    def create_assessment(
        self,
        payload: AcademicAssessmentCreateSchema,
        *,
        current_user: User,
    ) -> AcademicAssessmentResponseSchema:
        """Cadastra prova, microavaliação ou projeto validando turma, disciplina, módulo e alocação docente."""
        academic_class = self._repository.get_class_by_id(payload.class_id)
        if academic_class is None:
            raise NotFoundException(message=ASSESSMENT_CLASS_NOT_FOUND_MESSAGE)

        subject = self._repository.get_subject_by_id(payload.subject_id)
        if subject is None:
            raise NotFoundException(message=ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            )
        ):
            raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)

        if academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=ASSESSMENT_INACTIVE_CLASS_MESSAGE)

        if not subject.is_active:
            raise UnprocessableEntityException(message=ASSESSMENT_INACTIVE_SUBJECT_MESSAGE)

        if subject.course_id != academic_class.course_id:
            raise UnprocessableEntityException(
                message=ASSESSMENT_SUBJECT_COURSE_MISMATCH_MESSAGE
            )

        if payload.module_id is not None:
            module = self._repository.get_module_by_id(payload.module_id)
            if module is None:
                raise NotFoundException(message=ASSESSMENT_MODULE_NOT_FOUND_MESSAGE)
            if module.subject_id != subject.id:
                raise UnprocessableEntityException(
                    message=ASSESSMENT_MODULE_SUBJECT_MISMATCH_MESSAGE
                )

        created = self._repository.create_assessment(
            class_id=academic_class.id,
            subject_id=subject.id,
            module_id=payload.module_id,
            title=payload.title,
            assessment_type=payload.assessment_type,
            weight=payload.weight,
            application_date=payload.application_date,
            max_grade=payload.max_grade,
        )
        logger.bind(
            assessment_id=str(created.id),
            class_id=str(created.class_id),
            subject_id=str(created.subject_id),
            module_id=str(created.module_id) if created.module_id else None,
            assessment_type=created.assessment_type.value,
            weight=str(created.weight),
            actor_id=str(current_user.id),
        ).info("Avaliação formativa cadastrada com sucesso.")
        return self._to_assessment_response(created)

    def list_assessments(
        self,
        params: AcademicAssessmentListQueryParams,
        *,
        current_user: User,
    ) -> AcademicAssessmentPaginatedResponseSchema:
        """Lista avaliações formativas ordenadas por application_date com RBAC contextual."""
        allowed_class_ids: list[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            assigned_pairs = self._repository.get_teacher_assigned_class_subject_pairs(
                current_user.id
            )
            if not assigned_pairs:
                raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)
            assigned_classes = {cls_id for cls_id, _ in assigned_pairs}
            if params.class_id is not None and params.class_id not in assigned_classes:
                raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)
            if (
                params.class_id is not None
                and params.subject_id is not None
                and (params.class_id, params.subject_id) not in assigned_pairs
            ):
                raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)
            allowed_class_ids = list(assigned_classes)

        items, total = self._repository.list_assessments(
            page=params.page,
            limit=params.limit,
            class_id=params.class_id,
            subject_id=params.subject_id,
            module_id=params.module_id,
            assessment_type=params.assessment_type,
            allowed_class_ids=allowed_class_ids,
        )
        return AcademicAssessmentPaginatedResponseSchema(
            data=[self._to_assessment_response(item) for item in items],
            total=total,
            page=params.page,
            limit=params.limit,
        )

    def record_batch_grades(
        self,
        assessment_id: UUID,
        payload: BatchStudentGradesRequestSchema,
        *,
        current_user: User,
        ip_address: str | None = None,
    ) -> BatchStudentGradesResponseSchema:
        """Lança notas e recuperações em lote na turma e grava retificações em audit_logs (BE-027)."""
        assessment = self._repository.get_by_id(assessment_id)
        if assessment is None:
            raise NotFoundException(message=ASSESSMENT_NOT_FOUND_MESSAGE)

        if (
            current_user.role == UserRole.TEACHER
            and not self._repository.is_teacher_assigned_to_class_and_subject(
                teacher_id=current_user.id,
                class_id=assessment.class_id,
                subject_id=assessment.subject_id,
            )
        ):
            raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)

        if assessment.academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(message=ASSESSMENT_INACTIVE_CLASS_MESSAGE)

        enrollments_by_student = self._repository.get_enrollments_by_class(
            assessment.class_id
        )
        max_grade = Decimal(assessment.max_grade).quantize(_DECIMAL_QUANTIZER)
        validated_items: list[tuple[Enrollment, Decimal, Decimal | None, str | None]] = []

        for item in payload.grades:
            enrollment = enrollments_by_student.get(item.student_id)
            if enrollment is None:
                raise BadRequestException(message=GRADE_STUDENT_NOT_ENROLLED_MESSAGE)

            if enrollment.status != EnrollmentStatus.ACTIVE:
                raise BadRequestException(message=GRADE_INACTIVE_ENROLLMENT_MESSAGE)

            grade_val = Decimal(item.grade_value).quantize(_DECIMAL_QUANTIZER)
            recovery_val = (
                Decimal(item.recovery_grade).quantize(_DECIMAL_QUANTIZER)
                if item.recovery_grade is not None
                else None
            )
            if grade_val > max_grade or (
                recovery_val is not None and recovery_val > max_grade
            ):
                raise BadRequestException(message=GRADE_EXCEEDS_MAX_GRADE_MESSAGE)

            validated_items.append((enrollment, grade_val, recovery_val, item.comments))

        existing_by_student = self._repository.get_existing_grades_by_assessment(
            assessment.id
        )
        session = self._repository.session
        now = _utc_now()

        created_count = 0
        rectified_count = 0
        processed_records: list[tuple[StudentGrade, bool]] = []

        for enrollment, grade_val, recovery_val, comments in validated_items:
            existing = existing_by_student.get(enrollment.student_id)
            if existing is None:
                new_grade = StudentGrade(
                    assessment_id=assessment.id,
                    enrollment_id=enrollment.id,
                    student_id=enrollment.student_id,
                    recorded_by=current_user.id,
                    grade_value=grade_val,
                    recovery_grade=recovery_val,
                    comments=comments,
                )
                session.add(new_grade)
                session.flush()
                created_count += 1
                processed_records.append((new_grade, False))
            else:
                prev_grade_val = Decimal(existing.grade_value).quantize(_DECIMAL_QUANTIZER)
                prev_recovery_val = (
                    Decimal(existing.recovery_grade).quantize(_DECIMAL_QUANTIZER)
                    if existing.recovery_grade is not None
                    else None
                )
                prev_effective, _ = compute_senai_effective_grade(
                    prev_grade_val,
                    prev_recovery_val,
                )
                new_effective, _ = compute_senai_effective_grade(
                    grade_val,
                    recovery_val,
                )
                is_grade_changed = (
                    prev_grade_val != grade_val or prev_recovery_val != recovery_val
                )

                old_values = {
                    "assessment_id": str(assessment.id),
                    "student_id": str(enrollment.student_id),
                    "enrollment_id": str(enrollment.id),
                    "grade_value": str(prev_grade_val),
                    "recovery_grade": (
                        str(prev_recovery_val)
                        if prev_recovery_val is not None
                        else None
                    ),
                    "effective_grade": str(prev_effective),
                    "comments": existing.comments,
                    "recorded_by": str(existing.recorded_by),
                }

                existing.grade_value = grade_val
                existing.recovery_grade = recovery_val
                existing.comments = comments
                existing.recorded_by = current_user.id
                existing.updated_at = now
                session.add(existing)
                session.flush()

                was_rectified = False
                if is_grade_changed:
                    was_rectified = True
                    rectified_count += 1
                    new_values = {
                        "assessment_id": str(assessment.id),
                        "student_id": str(enrollment.student_id),
                        "enrollment_id": str(enrollment.id),
                        "grade_value": str(grade_val),
                        "recovery_grade": (
                            str(recovery_val) if recovery_val is not None else None
                        ),
                        "effective_grade": str(new_effective),
                        "comments": comments,
                        "recorded_by": str(current_user.id),
                    }
                    self._audit_service.log_action(
                        user_id=current_user.id,
                        action="STUDENT_GRADE_RECTIFIED",
                        entity="student_grades",
                        entity_id=str(existing.id),
                        old_values=old_values,
                        new_values=new_values,
                        ip_address=ip_address,
                        commit=False,
                    )

                processed_records.append((existing, was_rectified))

        session.commit()
        for grade_entity, _ in processed_records:
            session.refresh(grade_entity)

        grades_response = [
            self._to_grade_item_response(grade_entity, was_rectified=was_rectified)
            for grade_entity, was_rectified in processed_records
        ]

        logger.bind(
            assessment_id=str(assessment.id),
            class_id=str(assessment.class_id),
            subject_id=str(assessment.subject_id),
            actor_id=str(current_user.id),
            total_processed=len(grades_response),
            created_count=created_count,
            rectified_count=rectified_count,
        ).info("Notas de avaliação formativa lançadas em lote com auditoria de retificações.")

        return BatchStudentGradesResponseSchema(
            assessment_id=assessment.id,
            class_id=assessment.class_id,
            subject_id=assessment.subject_id,
            module_id=assessment.module_id,
            max_grade=assessment.max_grade,
            total_processed=len(grades_response),
            created_count=created_count,
            rectified_count=rectified_count,
            grades=grades_response,
        )


def get_academic_assessment_service(
    repository: AcademicAssessmentRepositoryDep,
    audit_service: AuditServiceDep,
) -> AcademicAssessmentService:
    """Provedor de injeção de dependência para AcademicAssessmentService."""
    return AcademicAssessmentService(
        repository=repository,
        audit_service=audit_service,
    )


AcademicAssessmentServiceDep = Annotated[
    AcademicAssessmentService,
    Depends(get_academic_assessment_service),
]

__all__ = [
    "ASSESSMENT_CLASS_NOT_FOUND_MESSAGE",
    "ASSESSMENT_INACTIVE_CLASS_MESSAGE",
    "ASSESSMENT_INACTIVE_SUBJECT_MESSAGE",
    "ASSESSMENT_MODULE_NOT_FOUND_MESSAGE",
    "ASSESSMENT_MODULE_SUBJECT_MISMATCH_MESSAGE",
    "ASSESSMENT_NOT_FOUND_MESSAGE",
    "ASSESSMENT_SUBJECT_COURSE_MISMATCH_MESSAGE",
    "ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE",
    "ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE",
    "AcademicAssessmentService",
    "AcademicAssessmentServiceDep",
    "GRADE_EXCEEDS_MAX_GRADE_MESSAGE",
    "GRADE_INACTIVE_ENROLLMENT_MESSAGE",
    "GRADE_STUDENT_NOT_ENROLLED_MESSAGE",
    "compute_senai_effective_grade",
    "get_academic_assessment_service",
]
