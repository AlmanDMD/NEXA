"""Serviço de domínio para Avaliações Formativas e Lançamento de Notas em Lote com Auditoria (BE-027)."""

from decimal import Decimal, ROUND_HALF_UP
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
from app.repositories.risk_engine_repository import RiskEngineRepository
from app.services.risk_engine_service import RiskEngineService
from app.schemas.academic_assessment import (
    AcademicAssessmentCreateSchema,
    AcademicAssessmentListQueryParams,
    AcademicAssessmentPaginatedResponseSchema,
    AcademicAssessmentResponseSchema,
    BatchStudentGradesRequestSchema,
    BatchStudentGradesResponseSchema,
    ClassGradesSummaryQueryParams,
    ClassGradesSummaryResponseSchema,
    StudentClassGradeReportSchema,
    StudentGradeItemResponseSchema,
    StudentModuleAverageSchema,
    StudentSubjectAverageSchema,
)
from app.schemas.class_lesson import (
    LessonModuleSummarySchema,
    LessonSubjectSummarySchema,
    StudentAttendanceSummaryStudentSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import (
    AcademicStandingStatus,
    ClassStatus,
    EnrollmentStatus,
    RiskLevel,
    UserRole,
)
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
CLASS_AVERAGES_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
CLASS_AVERAGES_CLOSED_CLASS_MESSAGE: Final[str] = (
    "Não é possível fechar ou recalcular médias em uma turma cujo período letivo não está ativo."
)
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")
_DEFAULT_PASSING_SCORE: Final[Decimal] = Decimal("6.00")
_PRACTICAL_TASK_DEFAULT_WEIGHT: Final[Decimal] = Decimal("1.00")
_AT_RISK_RECOVERY_MARGIN: Final[Decimal] = Decimal("2.00")
_ATTENDANCE_FAIL_THRESHOLD: Final[Decimal] = Decimal("75.00")
_ATTENDANCE_WARNING_THRESHOLD: Final[Decimal] = Decimal("78.00")


def _quantize_decimal(value: Decimal) -> Decimal:
    """Arredonda Decimal para duas casas decimais usando ROUND_HALF_UP."""
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _clamp_grade(value: Decimal) -> Decimal:
    """Limita uma média calculada ao intervalo [0.00, 10.00] com 2 casas decimais."""
    quantized = _quantize_decimal(value)
    return min(Decimal("10.00"), max(Decimal("0.00"), quantized))


def classify_academic_standing(
    average: Decimal | None,
    *,
    passing_score: Decimal = _DEFAULT_PASSING_SCORE,
    attendance_rate: Decimal | None = None,
) -> tuple[AcademicStandingStatus, RiskLevel, bool]:
    """Classifica situação acadêmica (APPROVED, IN_RECOVERY, AT_RISK) e nível de risco a partir da média e frequência."""
    normalized_passing = _quantize_decimal(Decimal(passing_score))
    critical_grade_threshold = max(
        Decimal("0.00"),
        normalized_passing - _AT_RISK_RECOVERY_MARGIN,
    )

    if average is None:
        if attendance_rate is not None and attendance_rate < _ATTENDANCE_FAIL_THRESHOLD:
            return AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, False
        if attendance_rate is not None and attendance_rate < _ATTENDANCE_WARNING_THRESHOLD:
            return AcademicStandingStatus.IN_RECOVERY, RiskLevel.HIGH, False
        return AcademicStandingStatus.IN_RECOVERY, RiskLevel.LOW, False

    normalized_avg = _quantize_decimal(Decimal(average))
    is_below_passing = normalized_avg < normalized_passing

    if not is_below_passing:
        if attendance_rate is not None and attendance_rate < _ATTENDANCE_FAIL_THRESHOLD:
            return AcademicStandingStatus.AT_RISK, RiskLevel.CRITICAL, False
        if attendance_rate is not None and attendance_rate < _ATTENDANCE_WARNING_THRESHOLD:
            return AcademicStandingStatus.APPROVED, RiskLevel.HIGH, False
        return AcademicStandingStatus.APPROVED, RiskLevel.LOW, False

    if normalized_avg < critical_grade_threshold or (
        attendance_rate is not None and attendance_rate < _ATTENDANCE_WARNING_THRESHOLD
    ):
        risk = (
            RiskLevel.CRITICAL
            if (
                normalized_avg < critical_grade_threshold
                or (
                    attendance_rate is not None
                    and attendance_rate < _ATTENDANCE_FAIL_THRESHOLD
                )
            )
            else RiskLevel.HIGH
        )
        return AcademicStandingStatus.AT_RISK, risk, True

    return AcademicStandingStatus.IN_RECOVERY, RiskLevel.MODERATE, True


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

    def _build_class_grades_report(
        self,
        class_id: UUID,
        *,
        current_user: User,
        persist_to_enrollments: bool,
        params: ClassGradesSummaryQueryParams | None = None,
    ) -> ClassGradesSummaryResponseSchema:
        """Consolida médias ponderadas por módulo, disciplina e aluno combinando student_grades e task_submissions (BE-028)."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=ASSESSMENT_CLASS_NOT_FOUND_MESSAGE)

        requested_subject_id = params.subject_id if params is not None else None
        requested_module_id = params.module_id if params is not None else None
        requested_student_id = params.student_id if params is not None else None
        requested_status = params.status if params is not None else None

        allowed_subject_ids: list[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            assigned_subject_ids = self._repository.get_teacher_assigned_subject_ids_for_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
            if not assigned_subject_ids:
                raise ForbiddenException(message=CLASS_AVERAGES_TEACHER_FORBIDDEN_MESSAGE)
            if (
                requested_subject_id is not None
                and requested_subject_id not in assigned_subject_ids
            ):
                raise ForbiddenException(message=ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE)
            if not persist_to_enrollments:
                allowed_subject_ids = list(assigned_subject_ids)

        if persist_to_enrollments and academic_class.status != ClassStatus.ACTIVE:
            raise UnprocessableEntityException(
                message=CLASS_AVERAGES_CLOSED_CLASS_MESSAGE
            )

        if requested_subject_id is not None:
            subject = self._repository.get_subject_by_id(requested_subject_id)
            if subject is None:
                raise NotFoundException(message=ASSESSMENT_SUBJECT_NOT_FOUND_MESSAGE)

        if requested_module_id is not None:
            module = self._repository.get_module_by_id(requested_module_id)
            if module is None:
                raise NotFoundException(message=ASSESSMENT_MODULE_NOT_FOUND_MESSAGE)

        enrollments = self._repository.list_class_enrollments_with_students(
            academic_class.id,
            student_id=requested_student_id,
            exclude_dropped=True,
        )
        enrollments.sort(
            key=lambda enr: (
                (
                    enr.student.profile.full_name.lower()
                    if enr.student.profile is not None
                    and enr.student.profile.full_name
                    else enr.student.email.lower()
                ),
                str(enr.student_id),
            )
        )

        subjects = self._repository.list_course_subjects_with_modules(
            academic_class.course_id,
            subject_id=requested_subject_id,
            allowed_subject_ids=allowed_subject_ids,
        )
        assessments = self._repository.list_class_assessments_with_grades(
            academic_class.id,
            subject_id=requested_subject_id,
            module_id=requested_module_id,
        )
        practical_tasks = self._repository.list_class_practical_tasks_with_submissions(
            academic_class.id,
            module_id=requested_module_id,
        )

        # Indexa avaliações formativas por (student_id, module_id) e subject-level (module_id=None)
        module_assessments_by_student: dict[
            tuple[UUID, UUID], list[tuple[Decimal, Decimal]]
        ] = {}
        unlinked_assessments_by_student_subject: dict[
            tuple[UUID, UUID], list[tuple[Decimal, Decimal]]
        ] = {}

        for assessment in assessments:
            weight = Decimal(assessment.weight)
            for grade in assessment.grades:
                effective, _ = compute_senai_effective_grade(
                    grade.grade_value,
                    grade.recovery_grade,
                )
                if assessment.module_id is not None:
                    module_assessments_by_student.setdefault(
                        (grade.student_id, assessment.module_id),
                        [],
                    ).append((effective, weight))
                else:
                    unlinked_assessments_by_student_subject.setdefault(
                        (grade.student_id, assessment.subject_id),
                        [],
                    ).append((effective, weight))

        # Indexa entregas práticas avaliadas (final_task_score != None) por (student_id, module_id)
        module_tasks_by_student: dict[tuple[UUID, UUID], list[Decimal]] = {}
        for task in practical_tasks:
            for sub in task.submissions:
                if sub.final_task_score is not None:
                    module_tasks_by_student.setdefault(
                        (sub.student_id, task.module_id),
                        [],
                    ).append(Decimal(sub.final_task_score))

        now = _utc_now()
        updated_enrollments_count = 0
        all_student_reports: list[StudentClassGradeReportSchema] = []

        for enrollment in enrollments:
            student = enrollment.student
            profile = student.profile
            student_summary = StudentAttendanceSummaryStudentSchema(
                id=student.id,
                email=student.email,
                full_name=profile.full_name if profile is not None else None,
                registration_number=(
                    profile.registration_number if profile is not None else None
                ),
            )

            student_subjects: list[StudentSubjectAverageSchema] = []
            student_modules_flat: list[StudentModuleAverageSchema] = []
            evaluated_subject_averages: list[Decimal] = []
            evaluated_passing_scores: list[Decimal] = []

            for subj in subjects:
                ordered_modules = sorted(
                    subj.learning_modules,
                    key=lambda mod: (mod.order_index, mod.title.lower(), str(mod.id)),
                )
                if requested_module_id is not None:
                    ordered_modules = [
                        mod for mod in ordered_modules if mod.id == requested_module_id
                    ]
                    if not ordered_modules:
                        continue

                subj_module_reports: list[StudentModuleAverageSchema] = []
                subj_weighted_sum = Decimal("0.00")
                subj_weight_total = Decimal("0.00")
                subj_passing_scores: list[Decimal] = []

                for mod in ordered_modules:
                    mod_passing = _quantize_decimal(Decimal(mod.passing_score))
                    mod_weight = _quantize_decimal(Decimal(mod.module_weight))
                    subj_passing_scores.append(mod_passing)

                    grade_entries = module_assessments_by_student.get(
                        (student.id, mod.id),
                        [],
                    )
                    task_scores = module_tasks_by_student.get(
                        (student.id, mod.id),
                        [],
                    )

                    assessments_weighted_num = Decimal("0.00")
                    assessments_weight_den = Decimal("0.00")
                    for eff_grade, a_weight in grade_entries:
                        assessments_weighted_num += eff_grade * a_weight
                        assessments_weight_den += a_weight

                    assessments_avg: Decimal | None = (
                        _clamp_grade(assessments_weighted_num / assessments_weight_den)
                        if assessments_weight_den > Decimal("0.00")
                        else None
                    )

                    tasks_weighted_num = Decimal("0.00")
                    tasks_weight_den = Decimal("0.00")
                    for t_score in task_scores:
                        tasks_weighted_num += t_score * _PRACTICAL_TASK_DEFAULT_WEIGHT
                        tasks_weight_den += _PRACTICAL_TASK_DEFAULT_WEIGHT

                    practical_avg: Decimal | None = (
                        _clamp_grade(tasks_weighted_num / tasks_weight_den)
                        if tasks_weight_den > Decimal("0.00")
                        else None
                    )

                    combined_num = assessments_weighted_num + tasks_weighted_num
                    combined_den = assessments_weight_den + tasks_weight_den
                    module_avg: Decimal | None = (
                        _clamp_grade(combined_num / combined_den)
                        if combined_den > Decimal("0.00")
                        else None
                    )

                    mod_status, _mod_risk, mod_below = classify_academic_standing(
                        module_avg,
                        passing_score=mod_passing,
                        attendance_rate=enrollment.attendance_rate,
                    )

                    mod_schema = StudentModuleAverageSchema(
                        module_id=mod.id,
                        subject_id=subj.id,
                        module_title=mod.title,
                        order_index=mod.order_index,
                        module_weight=mod_weight,
                        passing_score=mod_passing,
                        assessments_count=len(grade_entries),
                        practical_tasks_count=len(task_scores),
                        assessments_average=assessments_avg,
                        practical_tasks_average=practical_avg,
                        module_average=module_avg,
                        is_below_passing_score=mod_below,
                        status=mod_status,
                    )
                    subj_module_reports.append(mod_schema)
                    student_modules_flat.append(mod_schema)

                    if module_avg is not None:
                        subj_weighted_sum += module_avg * mod_weight
                        subj_weight_total += mod_weight
                        evaluated_passing_scores.append(mod_passing)

                # Avaliações formativas vinculadas diretamente à disciplina (module_id IS NULL)
                if requested_module_id is None:
                    unlinked_entries = unlinked_assessments_by_student_subject.get(
                        (student.id, subj.id),
                        [],
                    )
                    for eff_grade, a_weight in unlinked_entries:
                        subj_weighted_sum += eff_grade * a_weight
                        subj_weight_total += a_weight

                subj_passing = (
                    _quantize_decimal(
                        sum(subj_passing_scores, Decimal("0.00"))
                        / Decimal(len(subj_passing_scores))
                    )
                    if subj_passing_scores
                    else _DEFAULT_PASSING_SCORE
                )
                subj_avg: Decimal | None = (
                    _clamp_grade(subj_weighted_sum / subj_weight_total)
                    if subj_weight_total > Decimal("0.00")
                    else None
                )
                subj_status, _subj_risk, subj_below = classify_academic_standing(
                    subj_avg,
                    passing_score=subj_passing,
                    attendance_rate=enrollment.attendance_rate,
                )
                student_subjects.append(
                    StudentSubjectAverageSchema(
                        subject_id=subj.id,
                        subject_code=subj.code,
                        subject_name=subj.name,
                        passing_score=subj_passing,
                        subject_average=subj_avg,
                        is_below_passing_score=subj_below,
                        status=subj_status,
                        modules=subj_module_reports,
                    )
                )
                if subj_avg is not None:
                    evaluated_subject_averages.append(subj_avg)

            overall_passing = (
                _quantize_decimal(
                    sum(evaluated_passing_scores, Decimal("0.00"))
                    / Decimal(len(evaluated_passing_scores))
                )
                if evaluated_passing_scores
                else _DEFAULT_PASSING_SCORE
            )
            overall_final_grade: Decimal | None = (
                _clamp_grade(
                    sum(evaluated_subject_averages, Decimal("0.00"))
                    / Decimal(len(evaluated_subject_averages))
                )
                if evaluated_subject_averages
                else None
            )

            overall_status, overall_risk, overall_below = classify_academic_standing(
                overall_final_grade,
                passing_score=overall_passing,
                attendance_rate=enrollment.attendance_rate,
            )
            below_passing_modules = sum(
                1 for mod in student_modules_flat if mod.is_below_passing_score
            )

            if (
                persist_to_enrollments
                and enrollment.status == EnrollmentStatus.ACTIVE
                and overall_final_grade is not None
            ):
                enrollment.final_grade = overall_final_grade
                enrollment.updated_at = now
                self._repository.session.add(enrollment)
                updated_enrollments_count += 1

            if persist_to_enrollments and overall_status in (
                AcademicStandingStatus.AT_RISK,
                AcademicStandingStatus.IN_RECOVERY,
            ):
                logger.bind(
                    class_id=str(academic_class.id),
                    enrollment_id=str(enrollment.id),
                    student_id=str(student.id),
                    final_grade=str(overall_final_grade)
                    if overall_final_grade is not None
                    else None,
                    passing_score=str(overall_passing),
                    standing_status=overall_status.value,
                    risk_level=overall_risk.value,
                ).warning(
                    "Indicador de risco acadêmico acionado no fechamento de médias (hook RiskEngineService BE-032)."
                )

            all_student_reports.append(
                StudentClassGradeReportSchema(
                    enrollment_id=enrollment.id,
                    student_id=student.id,
                    enrollment_status=enrollment.status,
                    student=student_summary,
                    attendance_rate=enrollment.attendance_rate,
                    passing_score=overall_passing,
                    final_grade=overall_final_grade,
                    is_below_passing_score=overall_below,
                    status=overall_status,
                    risk_level=overall_risk,
                    below_passing_modules_count=below_passing_modules,
                    subjects=student_subjects,
                    modules=student_modules_flat,
                )
            )

        if persist_to_enrollments and updated_enrollments_count > 0:
            self._repository.session.commit()

        if persist_to_enrollments:
            RiskEngineService(
                repository=RiskEngineRepository(session=self._repository.session)
            ).evaluate_class_students_risk(class_id=academic_class.id)

        approved_count = sum(
            1
            for item in all_student_reports
            if item.status == AcademicStandingStatus.APPROVED
        )
        in_recovery_count = sum(
            1
            for item in all_student_reports
            if item.status == AcademicStandingStatus.IN_RECOVERY
        )
        at_risk_count = sum(
            1
            for item in all_student_reports
            if item.status == AcademicStandingStatus.AT_RISK
        )

        computed_grades = [
            item.final_grade
            for item in all_student_reports
            if item.final_grade is not None
        ]
        class_average_grade = (
            _clamp_grade(
                sum(computed_grades, Decimal("0.00")) / Decimal(len(computed_grades))
            )
            if computed_grades
            else None
        )

        if requested_status is not None:
            filtered_students = [
                item for item in all_student_reports if item.status == requested_status
            ]
        else:
            filtered_students = all_student_reports

        if persist_to_enrollments:
            logger.bind(
                class_id=str(academic_class.id),
                actor_id=str(current_user.id),
                total_students=len(all_student_reports),
                updated_enrollments_count=updated_enrollments_count,
                approved_count=approved_count,
                in_recovery_count=in_recovery_count,
                at_risk_count=at_risk_count,
                class_average_grade=str(class_average_grade)
                if class_average_grade is not None
                else None,
            ).info("Médias ponderadas da turma calculadas e consolidadas em enrollments.")

        return ClassGradesSummaryResponseSchema(
            class_id=academic_class.id,
            academic_class=EnrollmentClassSummarySchema.model_validate(academic_class),
            calculated_at=now,
            persisted_to_enrollments=persist_to_enrollments,
            updated_enrollments_count=updated_enrollments_count,
            total_students=len(all_student_reports),
            approved_count=approved_count,
            in_recovery_count=in_recovery_count,
            at_risk_count=at_risk_count,
            class_average_grade=class_average_grade,
            students=filtered_students,
        )

    def calculate_class_averages(
        self,
        class_id: UUID,
        *,
        current_user: User,
    ) -> ClassGradesSummaryResponseSchema:
        """Executa o fechamento de médias ponderadas da turma e atualiza enrollments.final_grade (BE-028)."""
        return self._build_class_grades_report(
            class_id,
            current_user=current_user,
            persist_to_enrollments=True,
            params=None,
        )

    def get_class_grades_summary(
        self,
        class_id: UUID,
        params: ClassGradesSummaryQueryParams | None = None,
        *,
        current_user: User,
    ) -> ClassGradesSummaryResponseSchema:
        """Retorna o boletim consolidado de médias da turma sem alterar enrollments (BE-028)."""
        return self._build_class_grades_report(
            class_id,
            current_user=current_user,
            persist_to_enrollments=False,
            params=params,
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
    "CLASS_AVERAGES_CLOSED_CLASS_MESSAGE",
    "CLASS_AVERAGES_TEACHER_FORBIDDEN_MESSAGE",
    "GRADE_EXCEEDS_MAX_GRADE_MESSAGE",
    "GRADE_INACTIVE_ENROLLMENT_MESSAGE",
    "GRADE_STUDENT_NOT_ENROLLED_MESSAGE",
    "classify_academic_standing",
    "compute_senai_effective_grade",
    "get_academic_assessment_service",
]
