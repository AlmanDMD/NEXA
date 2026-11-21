"""Serviço de domínio para Diário de Classe e Registro de Aulas Ministradas (BE-021)."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any, Final
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
    ModuleAttendanceRiskItemSchema,
    StudentAttendanceQueryParams,
    StudentAttendanceSummaryStudentSchema,
    StudentConsolidatedAttendanceResponseSchema,
    StudentLessonAbsenceRecordSchema,
    SubjectConsolidatedAttendanceSchema,
    UpdatedEnrollmentAttendanceSchema,
)
from app.schemas.enums import AttendanceStatus, ClassStatus, EnrollmentStatus, RiskLevel, UserRole

LESSON_NOT_FOUND_MESSAGE: Final[str] = "Aula não encontrada no diário de classe."
STUDENT_NOT_FOUND_MESSAGE: Final[str] = "Estudante não encontrado."
STUDENT_ENROLLMENT_NOT_FOUND_MESSAGE: Final[str] = (
    "Matrícula do estudante não encontrada para a turma informada."
)
STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso negado: estudantes só podem consultar seu próprio extrato de frequência."
)
STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona em nenhuma turma em que o estudante está matriculado."
)
ATTENDANCE_MAX_ABSENCE_RATIO: Final[Decimal] = Decimal("0.25")
_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")
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

    def get_student_consolidated_attendance(
        self,
        student_id: UUID,
        params: StudentAttendanceQueryParams | None = None,
        *,
        current_user: User,
    ) -> StudentConsolidatedAttendanceResponseSchema:
        """Retorna o extrato consolidado de frequência por disciplina e módulo consultando vw_module_attendance_risk (BE-023)."""
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            raise ForbiddenException(message=STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE)

        student = self._repository.get_user_by_id(student_id)
        if student is None or student.role != UserRole.STUDENT:
            raise NotFoundException(message=STUDENT_NOT_FOUND_MESSAGE)

        requested_class_id = params.class_id if params is not None else None
        requested_subject_id = params.subject_id if params is not None else None

        if requested_class_id is not None:
            academic_class = self._repository.get_class_by_id(requested_class_id)
            if academic_class is None:
                raise NotFoundException(message=LESSON_CLASS_NOT_FOUND_MESSAGE)
            if (
                current_user.role == UserRole.TEACHER
                and not self._repository.is_teacher_assigned_to_class(
                    teacher_id=current_user.id,
                    class_id=academic_class.id,
                )
            ):
                raise ForbiddenException(message=STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE)

        if requested_subject_id is not None:
            subject = self._repository.get_subject_by_id(requested_subject_id)
            if subject is None:
                raise NotFoundException(message=LESSON_SUBJECT_NOT_FOUND_MESSAGE)

        enrollments = self._repository.list_student_enrollments(
            student.id,
            class_id=requested_class_id,
        )
        if requested_class_id is not None and not enrollments:
            raise NotFoundException(message=STUDENT_ENROLLMENT_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER:
            student_class_ids = [enr.class_id for enr in enrollments]
            allowed_class_ids = self._repository.get_teacher_assigned_class_ids(
                current_user.id,
                class_ids=student_class_ids,
            )
            if not allowed_class_ids:
                raise ForbiddenException(message=STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE)
            enrollments = [enr for enr in enrollments if enr.class_id in allowed_class_ids]

        profile = student.profile
        student_summary = StudentAttendanceSummaryStudentSchema(
            id=student.id,
            email=student.email,
            full_name=profile.full_name if profile is not None else None,
            registration_number=(
                profile.registration_number if profile is not None else None
            ),
        )

        if not enrollments:
            empty_metrics = compute_attendance_margin_metrics(
                total_hours=0,
                attended_hours=0,
                absent_hours=0,
                planned_hours=0,
            )
            return StudentConsolidatedAttendanceResponseSchema(
                student_id=student.id,
                student=student_summary,
                enrollment_id=None,
                class_id=None,
                enrollment_status=None,
                planned_hours=0,
                total_hours=0,
                attended_hours=0,
                absent_hours=0,
                justified_absent_hours=0,
                **empty_metrics,
                critical_modules_count=0,
                subjects=[],
                modules=[],
                absence_records=[],
            )

        primary_enrollment = enrollments[0]
        enrollments_by_id = {enr.id: enr for enr in enrollments}
        enrollments_by_class = {enr.class_id: enr for enr in enrollments}
        target_class_ids = [enr.class_id for enr in enrollments]
        target_course_ids = [enr.academic_class.course_id for enr in enrollments]

        view_rows = self._repository.query_module_attendance_risk_view(
            student.id,
            class_ids=target_class_ids,
            subject_id=requested_subject_id,
        )
        record_rows = self._repository.list_student_attendance_records_with_lessons(
            student.id,
            class_ids=target_class_ids,
            subject_id=requested_subject_id,
        )
        course_subjects = self._repository.list_course_subjects_by_course_ids(
            target_course_ids,
            subject_id=requested_subject_id,
        )

        modules_list: list[ModuleAttendanceRiskItemSchema] = []
        modules_by_enrollment_subject: dict[
            tuple[UUID, UUID],
            list[ModuleAttendanceRiskItemSchema],
        ] = {}
        subject_meta_map: dict[
            tuple[UUID, UUID],
            tuple[str, str, str, str, int],
        ] = {}

        for enr in enrollments:
            for subj in course_subjects:
                if subj.course_id == enr.academic_class.course_id:
                    key = (enr.id, subj.id)
                    subject_meta_map[key] = (
                        enr.academic_class.code,
                        enr.academic_class.period,
                        subj.code,
                        subj.name,
                        int(subj.workload_hours),
                    )
                    modules_by_enrollment_subject.setdefault(key, [])

        for row in view_rows:
            enr_id = UUID(str(row["enrollment_id"]))
            cls_id = UUID(str(row["class_id"]))
            subj_id = UUID(str(row["subject_id"]))
            mod_id = UUID(str(row["module_id"]))
            class_code = str(row["class_code"])
            class_period = str(row["class_period"])
            subject_code = str(row["subject_code"])
            subject_name = str(row["subject_name"])
            subject_planned_hours = int(row["subject_planned_hours"] or 0)
            module_title = str(row["module_title"])
            module_order_index = int(row["module_order_index"])
            module_planned_hours = int(row["module_planned_hours"] or 0)
            total_h = int(row["total_hours"] or 0)
            attended_h = int(row["attended_hours"] or 0)
            absent_h = int(row["absent_hours"] or 0)
            justified_h = int(row["justified_absent_hours"] or 0)

            metrics = compute_attendance_margin_metrics(
                total_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                planned_hours=module_planned_hours,
            )
            mod_item = ModuleAttendanceRiskItemSchema(
                enrollment_id=enr_id,
                class_id=cls_id,
                class_code=class_code,
                class_period=class_period,
                subject_id=subj_id,
                subject_code=subject_code,
                subject_name=subject_name,
                module_id=mod_id,
                module_title=module_title,
                order_index=module_order_index,
                planned_hours=module_planned_hours,
                total_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                justified_absent_hours=justified_h,
                **metrics,
            )
            modules_list.append(mod_item)
            key = (enr_id, subj_id)
            subject_meta_map.setdefault(
                key,
                (
                    class_code,
                    class_period,
                    subject_code,
                    subject_name,
                    subject_planned_hours,
                ),
            )
            modules_by_enrollment_subject.setdefault(key, []).append(mod_item)

        unlinked_totals_by_enrollment_subject: dict[
            tuple[UUID, UUID],
            list[int],
        ] = {}
        absence_records: list[StudentLessonAbsenceRecordSchema] = []

        for att_record, lesson in record_rows:
            enr = enrollments_by_class.get(lesson.class_id)
            if enr is None:
                continue

            total_h = int(lesson.workload_hours)
            raw_absent = min(total_h, max(0, int(att_record.absent_hours)))
            if att_record.status in (AttendanceStatus.PRESENT, AttendanceStatus.JUSTIFIED):
                effective_absent = 0
            else:
                effective_absent = raw_absent
            justified_h = (
                raw_absent if att_record.status == AttendanceStatus.JUSTIFIED else 0
            )
            attended_h = max(0, total_h - effective_absent)

            if lesson.module_id is None:
                key = (enr.id, lesson.subject_id)
                bucket = unlinked_totals_by_enrollment_subject.setdefault(
                    key,
                    [0, 0, 0, 0],
                )
                bucket[0] += total_h
                bucket[1] += attended_h
                bucket[2] += effective_absent
                bucket[3] += justified_h

            if att_record.status != AttendanceStatus.PRESENT or raw_absent > 0:
                absence_records.append(
                    StudentLessonAbsenceRecordSchema(
                        attendance_record_id=att_record.id,
                        lesson_id=lesson.id,
                        class_id=lesson.class_id,
                        subject_id=lesson.subject_id,
                        subject_code=lesson.subject.code,
                        subject_name=lesson.subject.name,
                        module_id=lesson.module_id,
                        module_title=(
                            lesson.module.title if lesson.module is not None else None
                        ),
                        lesson_date=lesson.lesson_date,
                        workload_hours=lesson.workload_hours,
                        status=att_record.status,
                        absent_hours=raw_absent,
                        justification_note=att_record.justification_note,
                        recorded_at=att_record.recorded_at,
                    )
                )

        subjects_list: list[SubjectConsolidatedAttendanceSchema] = []
        overall_planned_hours = 0
        overall_total_hours = 0
        overall_attended_hours = 0
        overall_absent_hours = 0
        overall_justified_hours = 0

        for (enr_id, subj_id), meta in subject_meta_map.items():
            class_code, class_period, subject_code, subject_name, subject_planned = meta
            enr = enrollments_by_id[enr_id]
            subj_modules = sorted(
                modules_by_enrollment_subject.get((enr_id, subj_id), []),
                key=lambda item: (item.order_index, item.module_title.lower()),
            )
            unlinked = unlinked_totals_by_enrollment_subject.get(
                (enr_id, subj_id),
                [0, 0, 0, 0],
            )
            subj_total_h = sum(m.total_hours for m in subj_modules) + unlinked[0]
            subj_attended_h = sum(m.attended_hours for m in subj_modules) + unlinked[1]
            subj_absent_h = sum(m.absent_hours for m in subj_modules) + unlinked[2]
            subj_justified_h = (
                sum(m.justified_absent_hours for m in subj_modules) + unlinked[3]
            )
            resolved_subj_planned = max(
                subject_planned,
                sum(m.planned_hours for m in subj_modules),
            )
            subj_metrics = compute_attendance_margin_metrics(
                total_hours=subj_total_h,
                attended_hours=subj_attended_h,
                absent_hours=subj_absent_h,
                planned_hours=resolved_subj_planned,
            )
            subjects_list.append(
                SubjectConsolidatedAttendanceSchema(
                    enrollment_id=enr_id,
                    class_id=enr.class_id,
                    class_code=class_code,
                    class_period=class_period,
                    subject_id=subj_id,
                    subject_code=subject_code,
                    subject_name=subject_name,
                    planned_hours=resolved_subj_planned,
                    total_hours=subj_total_h,
                    attended_hours=subj_attended_h,
                    absent_hours=subj_absent_h,
                    justified_absent_hours=subj_justified_h,
                    **subj_metrics,
                    modules=subj_modules,
                )
            )
            overall_planned_hours += resolved_subj_planned
            overall_total_hours += subj_total_h
            overall_attended_hours += subj_attended_h
            overall_absent_hours += subj_absent_h
            overall_justified_hours += subj_justified_h

        overall_metrics = compute_attendance_margin_metrics(
            total_hours=overall_total_hours,
            attended_hours=overall_attended_hours,
            absent_hours=overall_absent_hours,
            planned_hours=overall_planned_hours,
        )
        critical_modules_count = sum(1 for mod in modules_list if mod.is_critical)

        return StudentConsolidatedAttendanceResponseSchema(
            student_id=student.id,
            student=student_summary,
            enrollment_id=primary_enrollment.id,
            class_id=primary_enrollment.class_id,
            enrollment_status=primary_enrollment.status,
            planned_hours=overall_planned_hours,
            total_hours=overall_total_hours,
            attended_hours=overall_attended_hours,
            absent_hours=overall_absent_hours,
            justified_absent_hours=overall_justified_hours,
            **overall_metrics,
            critical_modules_count=critical_modules_count,
            subjects=subjects_list,
            modules=modules_list,
            absence_records=absence_records,
        )


def compute_attendance_margin_metrics(
    *,
    total_hours: int,
    attended_hours: int,
    absent_hours: int,
    planned_hours: int,
) -> dict[str, Any]:
    """Calcula percentual de frequência, flags de risco (<78%) e margem restante até o limite de 75%."""
    if total_hours <= 0:
        attendance_percentage = Decimal("100.00")
    else:
        attendance_percentage = (
            (Decimal(attended_hours) * Decimal("100")) / Decimal(total_hours)
        ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

    is_critical, risk_level = evaluate_attendance_risk_level(attendance_percentage)
    max_allowed_absent_hours = (
        Decimal(max(0, total_hours)) * ATTENDANCE_MAX_ABSENCE_RATIO
    ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)
    remaining_absent_hours_margin = max(
        Decimal("0.00"),
        (max_allowed_absent_hours - Decimal(max(0, absent_hours))).quantize(
            _DECIMAL_QUANTIZER,
            rounding=ROUND_HALF_UP,
        ),
    )

    reference_planned_hours = max(0, planned_hours, total_hours)
    planned_max_allowed_absent_hours = (
        Decimal(reference_planned_hours) * ATTENDANCE_MAX_ABSENCE_RATIO
    ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)
    planned_remaining_absent_hours_margin = max(
        Decimal("0.00"),
        (planned_max_allowed_absent_hours - Decimal(max(0, absent_hours))).quantize(
            _DECIMAL_QUANTIZER,
            rounding=ROUND_HALF_UP,
        ),
    )
    percentage_margin_to_limit = (
        attendance_percentage - ATTENDANCE_FAIL_THRESHOLD
    ).quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)

    return {
        "attendance_percentage": attendance_percentage,
        "is_critical": is_critical,
        "is_attendance_critical": is_critical,
        "risk_level": risk_level,
        "min_required_percentage": ATTENDANCE_FAIL_THRESHOLD,
        "max_allowed_absent_hours": max_allowed_absent_hours,
        "remaining_absent_hours_margin": remaining_absent_hours_margin,
        "planned_max_allowed_absent_hours": planned_max_allowed_absent_hours,
        "planned_remaining_absent_hours_margin": planned_remaining_absent_hours_margin,
        "percentage_margin_to_limit": percentage_margin_to_limit,
    }


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
    "ATTENDANCE_MAX_ABSENCE_RATIO",
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
    "STUDENT_ATTENDANCE_IDOR_FORBIDDEN_MESSAGE",
    "STUDENT_ATTENDANCE_TEACHER_FORBIDDEN_MESSAGE",
    "STUDENT_ENROLLMENT_NOT_FOUND_MESSAGE",
    "STUDENT_NOT_FOUND_MESSAGE",
    "compute_attendance_margin_metrics",
    "evaluate_attendance_risk_level",
    "get_class_lesson_service",
]
