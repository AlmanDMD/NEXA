"""Serviço de domínio para Dashboard Híbrido do Professor e Visão 360° do Aluno (BE-031)."""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Any, Final
from uuid import UUID

from fastapi import Depends

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.base import _utc_now
from app.models.user import User
from app.repositories.dashboard_repository import (
    DashboardRepository,
    DashboardRepositoryDep,
)
from app.schemas.academic_assessment import (
    StudentModuleAverageSchema,
    StudentSubjectAverageSchema,
)
from app.schemas.class_lesson import (
    ModuleAttendanceRiskItemSchema,
    SubjectConsolidatedAttendanceSchema,
)
from app.schemas.dashboard import (
    DashboardStudent360SummaryItemSchema,
    DashboardStudentProfileSchema,
    ModuleDashboardPerformanceSchema,
    Student360OverviewResponseSchema,
    Student360QueryParams,
    StudentActiveAlertItemSchema,
    StudentCompetencyRadarItemSchema,
    StudentMilestoneTimelineItemSchema,
    StudentModuleProgressItemSchema,
    StudentPortalAttendanceSummarySchema,
    StudentPortalDashboardQueryParams,
    StudentPortalDashboardResponseSchema,
    TeacherClassDashboardQueryParams,
    TeacherClassDashboardResponseSchema,
    TeacherDashboardKpisSchema,
)
from app.schemas.enrollment import EnrollmentClassSummarySchema
from app.schemas.enums import (
    AcademicStandingStatus,
    EnrollmentStatus,
    RiskLevel,
    SubmissionStatus,
    UserRole,
)
from app.schemas.practical_task import (
    StudentPendingTaskItemSchema,
    StudentTaskCountsSummarySchema,
)
from app.services.academic_assessment_service import (
    classify_academic_standing,
    compute_senai_effective_grade,
)
from app.services.class_lesson_service import compute_attendance_margin_metrics
from app.services.practical_task_service import PracticalTaskService

DASHBOARD_CLASS_NOT_FOUND_MESSAGE: Final[str] = "Turma acadêmica não encontrada."
DASHBOARD_SUBJECT_NOT_FOUND_MESSAGE: Final[str] = "Disciplina técnica não encontrada."
DASHBOARD_MODULE_NOT_FOUND_MESSAGE: Final[str] = (
    "Módulo de aprendizagem prática não encontrado."
)
DASHBOARD_STUDENT_NOT_FOUND_MESSAGE: Final[str] = "Estudante não encontrado."
DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE: Final[str] = (
    "Matrícula do estudante não encontrada para a turma informada."
)
DASHBOARD_TEACHER_CLASS_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não possui atribuição ativa nesta turma."
)
DASHBOARD_TEACHER_SUBJECT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona a disciplina informada nesta turma."
)
DASHBOARD_TEACHER_STUDENT_FORBIDDEN_MESSAGE: Final[str] = (
    "Acesso não autorizado: professor não leciona em nenhuma turma em que o estudante está matriculado."
)

_DECIMAL_QUANTIZER: Final[Decimal] = Decimal("0.01")
_DEFAULT_PASSING_SCORE: Final[Decimal] = Decimal("6.00")
_PRACTICAL_TASK_WEIGHT: Final[Decimal] = Decimal("1.00")


def _q2(value: Decimal) -> Decimal:
    """Arredonda Decimal para duas casas decimais com ROUND_HALF_UP."""
    return value.quantize(_DECIMAL_QUANTIZER, rounding=ROUND_HALF_UP)


def _to_decimal_or_none(raw: Any) -> Decimal | None:
    """Converte valor numérico vindo de view SQL (Decimal, float, int, str) em Decimal(0.01)."""
    if raw is None:
        return None
    if isinstance(raw, Decimal):
        return _q2(raw)
    return _q2(Decimal(str(raw)))


def _to_date(raw: Any) -> date:
    """Converte valor de coluna DATE vindo de view SQL (date ou ISO string) em objeto date."""
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw)[:10])


def _compute_median(values: list[Decimal]) -> Decimal | None:
    """Calcula a mediana exata em Decimal(0.01) para uma lista de valores."""
    if not values:
        return None
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return _q2(ordered[mid])
    return _q2((ordered[mid - 1] + ordered[mid]) / Decimal("2"))


class DashboardService:
    """Serviço de agregação analítica para o Dashboard do Professor e Ficha 360° do Aluno (BE-031)."""

    def __init__(self, repository: DashboardRepository) -> None:
        self._repository = repository

    @staticmethod
    def _map_view_row_to_student_summary(
        row: dict[str, Any],
    ) -> DashboardStudent360SummaryItemSchema:
        """Converte uma linha da view vw_student_360_performance em DashboardStudent360SummaryItemSchema."""
        overall_avg = _to_decimal_or_none(row.get("overall_average"))
        parsed_att = _to_decimal_or_none(row.get("attendance_percentage"))
        attendance_pct = (
            parsed_att if parsed_att is not None else Decimal("100.00")
        )
        total_tasks = int(row.get("total_tasks_count") or 0)
        pending_tasks = int(row.get("pending_tasks_count") or 0)
        late_tasks = int(row.get("late_tasks_count") or 0)
        submitted_tasks = int(row.get("submitted_tasks_count") or 0)
        evaluated_tasks = int(row.get("evaluated_tasks_count") or 0)
        completed_tasks = int(row.get("completed_tasks_count") or 0)
        on_time_completed = int(row.get("on_time_completed_tasks_count") or 0)
        active_alerts = int(row.get("active_alerts_count") or 0)

        on_time_pct = (
            _q2((Decimal(on_time_completed) * Decimal("100")) / Decimal(total_tasks))
            if total_tasks > 0
            else Decimal("0.00")
        )

        standing_status, computed_risk, _ = classify_academic_standing(
            overall_avg,
            passing_score=_DEFAULT_PASSING_SCORE,
            attendance_rate=attendance_pct,
        )
        raw_view_risk = str(row.get("risk_level") or RiskLevel.LOW.value)
        view_risk = RiskLevel(raw_view_risk)

        risk_rank = {
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }
        resolved_risk = (
            view_risk
            if risk_rank[view_risk] >= risk_rank[computed_risk]
            else computed_risk
        )

        return DashboardStudent360SummaryItemSchema(
            enrollment_id=UUID(str(row["enrollment_id"])),
            student_id=UUID(str(row["student_id"])),
            student_email=str(row["student_email"]),
            student_full_name=(
                str(row["student_full_name"])
                if row.get("student_full_name") is not None
                else None
            ),
            registration_number=(
                str(row["registration_number"])
                if row.get("registration_number") is not None
                else None
            ),
            avatar_url=(
                str(row["avatar_url"]) if row.get("avatar_url") is not None else None
            ),
            class_id=UUID(str(row["class_id"])),
            class_code=str(row["class_code"]),
            class_period=str(row["class_period"]),
            enrollment_status=EnrollmentStatus(str(row["enrollment_status"])),
            enrollment_date=_to_date(row["enrollment_date"]),
            overall_average=overall_avg,
            attendance_percentage=attendance_pct,
            total_tasks_count=total_tasks,
            pending_tasks_count=pending_tasks,
            late_tasks_count=late_tasks,
            submitted_tasks_count=submitted_tasks,
            evaluated_tasks_count=evaluated_tasks,
            completed_tasks_count=completed_tasks,
            on_time_completed_tasks_count=on_time_completed,
            on_time_tasks_percentage=on_time_pct,
            active_alerts_count=active_alerts,
            standing_status=standing_status,
            risk_level=resolved_risk,
            is_at_risk=(resolved_risk != RiskLevel.LOW),
        )

    def get_teacher_class_dashboard(
        self,
        class_id: UUID,
        params: TeacherClassDashboardQueryParams | None = None,
        *,
        current_user: User,
    ) -> TeacherClassDashboardResponseSchema:
        """Consolida KPIs globais, distribuição por módulo e indicadores 360° da turma (< 150ms via DB-036/DB-037)."""
        academic_class = self._repository.get_class_by_id(class_id)
        if academic_class is None:
            raise NotFoundException(message=DASHBOARD_CLASS_NOT_FOUND_MESSAGE)

        requested_subject_id = params.subject_id if params is not None else None
        requested_module_id = params.module_id if params is not None else None

        allowed_subject_ids: list[UUID] | None = None
        if current_user.role == UserRole.TEACHER:
            assigned_subjects = self._repository.get_teacher_assigned_subject_ids_for_class(
                teacher_id=current_user.id,
                class_id=academic_class.id,
            )
            if not assigned_subjects:
                raise ForbiddenException(
                    message=DASHBOARD_TEACHER_CLASS_FORBIDDEN_MESSAGE
                )
            if (
                requested_subject_id is not None
                and requested_subject_id not in assigned_subjects
            ):
                raise ForbiddenException(
                    message=DASHBOARD_TEACHER_SUBJECT_FORBIDDEN_MESSAGE
                )
            allowed_subject_ids = list(assigned_subjects)

        if requested_subject_id is not None:
            if self._repository.get_subject_by_id(requested_subject_id) is None:
                raise NotFoundException(message=DASHBOARD_SUBJECT_NOT_FOUND_MESSAGE)

        if requested_module_id is not None:
            if self._repository.get_module_by_id(requested_module_id) is None:
                raise NotFoundException(message=DASHBOARD_MODULE_NOT_FOUND_MESSAGE)

        now = _utc_now()
        view_rows = self._repository.query_class_student_360_view(
            academic_class.id,
            exclude_dropped=True,
        )
        students_list = [
            self._map_view_row_to_student_summary(row) for row in view_rows
        ]
        active_student_ids = {item.student_id for item in students_list}

        # Agregação dos KPIs globais a partir de vw_student_360_performance
        total_students = len(students_list)
        valid_grades = [
            item.overall_average
            for item in students_list
            if item.overall_average is not None
        ]
        class_avg_grade = (
            _q2(sum(valid_grades, Decimal("0.00")) / Decimal(len(valid_grades)))
            if valid_grades
            else None
        )
        avg_attendance = (
            _q2(
                sum(
                    (item.attendance_percentage for item in students_list),
                    Decimal("0.00"),
                )
                / Decimal(total_students)
            )
            if total_students > 0
            else Decimal("100.00")
        )

        total_tasks_sum = sum(item.total_tasks_count for item in students_list)
        completed_tasks_sum = sum(item.completed_tasks_count for item in students_list)
        on_time_tasks_sum = sum(
            item.on_time_completed_tasks_count for item in students_list
        )

        on_time_pct = (
            _q2((Decimal(on_time_tasks_sum) * Decimal("100")) / Decimal(total_tasks_sum))
            if total_tasks_sum > 0
            else Decimal("0.00")
        )
        completed_pct = (
            _q2((Decimal(completed_tasks_sum) * Decimal("100")) / Decimal(total_tasks_sum))
            if total_tasks_sum > 0
            else Decimal("0.00")
        )

        at_risk_count = sum(1 for item in students_list if item.is_at_risk)
        critical_count = sum(
            1 for item in students_list if item.risk_level == RiskLevel.CRITICAL
        )
        active_alerts_sum = sum(item.active_alerts_count for item in students_list)

        kpis = TeacherDashboardKpisSchema(
            total_students=total_students,
            class_average_grade=class_avg_grade,
            average_attendance_rate=avg_attendance,
            on_time_tasks_percentage=on_time_pct,
            completed_tasks_percentage=completed_pct,
            at_risk_students_count=at_risk_count,
            critical_students_count=critical_count,
            active_alerts_count=active_alerts_sum,
        )

        # Distribuição modular (Desenho Técnico, Metrologia, Tornearia, etc.)
        subjects = self._repository.list_course_subjects_with_modules_and_competencies(
            academic_class.course_id,
            subject_id=requested_subject_id,
            allowed_subject_ids=allowed_subject_ids,
        )
        mod_attendance_rows = self._repository.query_class_module_attendance_view(
            academic_class.id,
            subject_id=requested_subject_id,
            module_id=requested_module_id,
            exclude_dropped=True,
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
        skill_evidences = self._repository.list_skill_evidences_for_students(
            list(active_student_ids)
        )

        # Indexa presença por module_id
        att_by_module: dict[UUID, list[tuple[UUID, Decimal, bool]]] = {}
        for att_row in mod_attendance_rows:
            m_id = UUID(str(att_row["module_id"]))
            s_id = UUID(str(att_row["student_id"]))
            parsed_mod_pct = _to_decimal_or_none(att_row.get("attendance_percentage"))
            pct = (
                parsed_mod_pct if parsed_mod_pct is not None else Decimal("100.00")
            )
            is_crit = bool(att_row.get("is_attendance_critical"))
            att_by_module.setdefault(m_id, []).append((s_id, pct, is_crit))

        # Indexa notas formativas por (module_id, student_id)
        grades_by_mod_student: dict[
            tuple[UUID, UUID], list[tuple[Decimal, Decimal]]
        ] = {}
        for assessment in assessments:
            if assessment.module_id is None:
                continue
            w = Decimal(assessment.weight)
            for grade in assessment.grades:
                if grade.student_id not in active_student_ids:
                    continue
                eff, _ = compute_senai_effective_grade(
                    grade.grade_value,
                    grade.recovery_grade,
                )
                grades_by_mod_student.setdefault(
                    (assessment.module_id, grade.student_id),
                    [],
                ).append((eff, w))

        # Indexa submissões práticas por module_id e por (module_id, student_id)
        task_scores_by_mod_student: dict[tuple[UUID, UUID], list[Decimal]] = {}
        task_counters_by_module: dict[UUID, list[int]] = {}  # [total, completed, on_time, late]
        for task in practical_tasks:
            counters = task_counters_by_module.setdefault(task.module_id, [0, 0, 0, 0])
            for sub in task.submissions:
                if sub.student_id not in active_student_ids:
                    continue
                counters[0] += 1
                eff_status = PracticalTaskService.resolve_effective_submission_status(
                    sub,
                    due_date=task.due_date,
                    reference_now=now,
                )
                if eff_status in (SubmissionStatus.SUBMITTED, SubmissionStatus.EVALUATED):
                    counters[1] += 1
                    if sub.completed_at is None or sub.completed_at <= task.due_date:
                        counters[2] += 1
                elif eff_status == SubmissionStatus.LATE:
                    counters[3] += 1

                if sub.final_task_score is not None:
                    task_scores_by_mod_student.setdefault(
                        (task.module_id, sub.student_id),
                        [],
                    ).append(Decimal(sub.final_task_score))

        # Indexa skill_evidences por competency_id
        evidences_by_comp: dict[UUID, list[Decimal]] = {}
        for ev in skill_evidences:
            evidences_by_comp.setdefault(ev.competency_id, []).append(
                Decimal(ev.verified_level)
            )

        modules_distribution: list[ModuleDashboardPerformanceSchema] = []
        for subj in subjects:
            ordered_mods = sorted(
                subj.learning_modules,
                key=lambda m: (m.order_index, m.title.lower(), str(m.id)),
            )
            for mod in ordered_mods:
                if requested_module_id is not None and mod.id != requested_module_id:
                    continue

                mod_passing = _q2(Decimal(mod.passing_score))
                student_mod_grades: list[Decimal] = []
                at_risk_in_mod: set[UUID] = set()

                for s_id in active_student_ids:
                    g_list = grades_by_mod_student.get((mod.id, s_id), [])
                    t_list = task_scores_by_mod_student.get((mod.id, s_id), [])
                    num = sum((val * w for val, w in g_list), Decimal("0.00")) + sum(
                        (val * _PRACTICAL_TASK_WEIGHT for val in t_list),
                        Decimal("0.00"),
                    )
                    den = sum((w for _, w in g_list), Decimal("0.00")) + (
                        Decimal(len(t_list)) * _PRACTICAL_TASK_WEIGHT
                    )
                    if den > Decimal("0.00"):
                        s_avg = _q2(num / den)
                        student_mod_grades.append(s_avg)
                        if s_avg < mod_passing:
                            at_risk_in_mod.add(s_id)

                att_entries = att_by_module.get(mod.id, [])
                for s_id, _pct, is_crit in att_entries:
                    if is_crit:
                        at_risk_in_mod.add(s_id)

                mod_avg_att = (
                    _q2(
                        sum((pct for _, pct, _ in att_entries), Decimal("0.00"))
                        / Decimal(len(att_entries))
                    )
                    if att_entries
                    else Decimal("100.00")
                )

                mod_avg_grade = (
                    _q2(
                        sum(student_mod_grades, Decimal("0.00"))
                        / Decimal(len(student_mod_grades))
                    )
                    if student_mod_grades
                    else None
                )
                mod_median_grade = _compute_median(student_mod_grades)

                m_total, m_comp, m_ontime, m_late = task_counters_by_module.get(
                    mod.id,
                    [0, 0, 0, 0],
                )
                mod_comp_rate = (
                    _q2((Decimal(m_comp) * Decimal("100")) / Decimal(m_total))
                    if m_total > 0
                    else Decimal("0.00")
                )
                mod_ontime_rate = (
                    _q2((Decimal(m_ontime) * Decimal("100")) / Decimal(m_total))
                    if m_total > 0
                    else Decimal("0.00")
                )

                mod_skill_values: list[Decimal] = []
                for mc in mod.module_competencies:
                    mod_skill_values.extend(evidences_by_comp.get(mc.competency_id, []))
                mod_avg_skill = (
                    _q2(
                        sum(mod_skill_values, Decimal("0.00"))
                        / Decimal(len(mod_skill_values))
                    )
                    if mod_skill_values
                    else None
                )

                modules_distribution.append(
                    ModuleDashboardPerformanceSchema(
                        module_id=mod.id,
                        subject_id=subj.id,
                        subject_code=subj.code,
                        subject_name=subj.name,
                        module_title=mod.title,
                        order_index=mod.order_index,
                        practical_hours=mod.practical_hours,
                        passing_score=mod_passing,
                        average_grade=mod_avg_grade,
                        median_grade=mod_median_grade,
                        average_attendance_rate=mod_avg_att,
                        completion_rate=mod_comp_rate,
                        on_time_completion_rate=mod_ontime_rate,
                        total_tasks_assigned=m_total,
                        completed_tasks_count=m_comp,
                        late_tasks_count=m_late,
                        average_skill_level=mod_avg_skill,
                        at_risk_students_count=len(at_risk_in_mod),
                    )
                )

        return TeacherClassDashboardResponseSchema(
            class_id=academic_class.id,
            academic_class=EnrollmentClassSummarySchema.model_validate(academic_class),
            course_code=academic_class.course.code,
            course_name=academic_class.course.name,
            generated_at=now,
            kpis=kpis,
            modules_distribution=modules_distribution,
            students=students_list,
        )

    def get_student_360_overview(
        self,
        student_id: UUID,
        params: Student360QueryParams | None = None,
        *,
        current_user: User,
    ) -> Student360OverviewResponseSchema:
        """Retorna a Ficha 360° multidisciplinar completa do estudante consultando DB-036 e DB-037 (BE-031)."""
        student = self._repository.get_user_by_id(student_id)
        if student is None or student.role != UserRole.STUDENT:
            raise NotFoundException(message=DASHBOARD_STUDENT_NOT_FOUND_MESSAGE)

        requested_class_id = params.class_id if params is not None else None
        if requested_class_id is not None:
            if self._repository.get_class_by_id(requested_class_id) is None:
                raise NotFoundException(message=DASHBOARD_CLASS_NOT_FOUND_MESSAGE)

        enrollments = self._repository.list_student_enrollments(
            student.id,
            class_id=requested_class_id,
        )
        if requested_class_id is not None and not enrollments:
            raise NotFoundException(message=DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE)

        if current_user.role == UserRole.TEACHER:
            student_class_ids = [enr.class_id for enr in enrollments]
            allowed_classes = self._repository.get_teacher_assigned_class_ids(
                current_user.id,
                class_ids=student_class_ids,
            )
            if not allowed_classes:
                raise ForbiddenException(
                    message=DASHBOARD_TEACHER_STUDENT_FORBIDDEN_MESSAGE
                )
            enrollments = [
                enr for enr in enrollments if enr.class_id in allowed_classes
            ]

        profile = student.profile
        student_profile = DashboardStudentProfileSchema(
            id=student.id,
            email=student.email,
            full_name=profile.full_name if profile is not None else None,
            registration_number=(
                profile.registration_number if profile is not None else None
            ),
            avatar_url=profile.avatar_url if profile is not None else None,
        )
        now = _utc_now()

        if not enrollments:
            return Student360OverviewResponseSchema(
                student_id=student.id,
                student=student_profile,
                enrollment_id=None,
                class_id=None,
                enrollment_status=None,
                academic_class=None,
                generated_at=now,
                overview=None,
                subjects=[],
                attendance_by_module=[],
                competencies=[],
                practical_submissions=[],
                active_alerts=[],
            )

        primary_enrollment = enrollments[0]
        academic_class = primary_enrollment.academic_class

        view_360_row = self._repository.query_student_360_view_by_enrollment(
            primary_enrollment.id
        )
        overview = (
            self._map_view_row_to_student_summary(view_360_row)
            if view_360_row is not None
            else None
        )

        # Frequência por módulo via vw_module_attendance_risk (DB-037)
        att_rows = self._repository.query_class_module_attendance_view(
            academic_class.id,
            student_id=student.id,
            exclude_dropped=False,
        )
        attendance_by_module: list[ModuleAttendanceRiskItemSchema] = []
        for row in att_rows:
            total_h = int(row["total_hours"] or 0)
            attended_h = int(row["attended_hours"] or 0)
            absent_h = int(row["absent_hours"] or 0)
            justified_h = int(row["justified_absent_hours"] or 0)
            planned_h = int(row["module_planned_hours"] or 0)
            metrics = compute_attendance_margin_metrics(
                total_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                planned_hours=planned_h,
            )
            attendance_by_module.append(
                ModuleAttendanceRiskItemSchema(
                    enrollment_id=UUID(str(row["enrollment_id"])),
                    class_id=UUID(str(row["class_id"])),
                    class_code=str(row["class_code"]),
                    class_period=str(row["class_period"]),
                    subject_id=UUID(str(row["subject_id"])),
                    subject_code=str(row["subject_code"]),
                    subject_name=str(row["subject_name"]),
                    module_id=UUID(str(row["module_id"])),
                    module_title=str(row["module_title"]),
                    order_index=int(row["module_order_index"]),
                    planned_hours=planned_h,
                    total_hours=total_h,
                    attended_hours=attended_h,
                    absent_hours=absent_h,
                    justified_absent_hours=justified_h,
                    **metrics,
                )
            )

        # Desempenho multidisciplinar (notas formativas + entregas práticas) e competências
        subjects = self._repository.list_course_subjects_with_modules_and_competencies(
            academic_class.course_id
        )
        assessments = self._repository.list_class_assessments_with_grades(
            academic_class.id
        )
        detailed_submissions = self._repository.list_student_detailed_submissions(
            student.id,
            class_id=academic_class.id,
        )
        skill_evidences = self._repository.list_skill_evidences_for_students(
            [student.id]
        )
        active_alerts_orm = self._repository.list_student_active_alerts(
            student.id,
            class_id=academic_class.id,
        )

        mod_grades: dict[UUID, list[tuple[Decimal, Decimal]]] = {}
        subj_unlinked_grades: dict[UUID, list[tuple[Decimal, Decimal]]] = {}
        for assessment in assessments:
            w = Decimal(assessment.weight)
            for grade in assessment.grades:
                if grade.student_id != student.id:
                    continue
                eff, _ = compute_senai_effective_grade(
                    grade.grade_value,
                    grade.recovery_grade,
                )
                if assessment.module_id is not None:
                    mod_grades.setdefault(assessment.module_id, []).append((eff, w))
                else:
                    subj_unlinked_grades.setdefault(assessment.subject_id, []).append(
                        (eff, w)
                    )

        mod_task_scores: dict[UUID, list[Decimal]] = {}
        practical_submissions_schemas = []
        for sub in detailed_submissions:
            eff_status = PracticalTaskService.resolve_effective_submission_status(
                sub,
                due_date=sub.task.due_date,
                reference_now=now,
            )
            practical_submissions_schemas.append(
                PracticalTaskService._to_student_pending_task_item(
                    sub,
                    effective_status=eff_status,
                )
            )
            if sub.final_task_score is not None:
                mod_task_scores.setdefault(sub.task.module_id, []).append(
                    Decimal(sub.final_task_score)
                )

        subjects_report: list[StudentSubjectAverageSchema] = []
        competency_targets: dict[UUID, tuple[str, str, Any, int]] = {}

        for subj in subjects:
            ordered_mods = sorted(
                subj.learning_modules,
                key=lambda m: (m.order_index, m.title.lower(), str(m.id)),
            )
            mod_reports: list[StudentModuleAverageSchema] = []
            subj_w_sum = Decimal("0.00")
            subj_w_den = Decimal("0.00")
            subj_passings: list[Decimal] = []

            for mod in ordered_mods:
                for mc in mod.module_competencies:
                    prev = competency_targets.get(mc.competency_id)
                    req_lvl = (
                        max(prev[3], mc.required_level)
                        if prev is not None
                        else mc.required_level
                    )
                    competency_targets[mc.competency_id] = (
                        mc.competency.code,
                        mc.competency.title,
                        mc.competency.category,
                        req_lvl,
                    )

                mod_passing = _q2(Decimal(mod.passing_score))
                mod_weight = _q2(Decimal(mod.module_weight))
                subj_passings.append(mod_passing)

                g_entries = mod_grades.get(mod.id, [])
                t_scores = mod_task_scores.get(mod.id, [])

                a_num = sum((val * w for val, w in g_entries), Decimal("0.00"))
                a_den = sum((w for _, w in g_entries), Decimal("0.00"))
                a_avg = _q2(a_num / a_den) if a_den > Decimal("0.00") else None

                t_num = sum(
                    (val * _PRACTICAL_TASK_WEIGHT for val in t_scores),
                    Decimal("0.00"),
                )
                t_den = Decimal(len(t_scores)) * _PRACTICAL_TASK_WEIGHT
                t_avg = _q2(t_num / t_den) if t_den > Decimal("0.00") else None

                c_den = a_den + t_den
                m_avg = _q2((a_num + t_num) / c_den) if c_den > Decimal("0.00") else None

                m_status, _, m_below = classify_academic_standing(
                    m_avg,
                    passing_score=mod_passing,
                    attendance_rate=primary_enrollment.attendance_rate,
                )
                mod_reports.append(
                    StudentModuleAverageSchema(
                        module_id=mod.id,
                        subject_id=subj.id,
                        module_title=mod.title,
                        order_index=mod.order_index,
                        module_weight=mod_weight,
                        passing_score=mod_passing,
                        assessments_count=len(g_entries),
                        practical_tasks_count=len(t_scores),
                        assessments_average=a_avg,
                        practical_tasks_average=t_avg,
                        module_average=m_avg,
                        is_below_passing_score=m_below,
                        status=m_status,
                    )
                )
                if m_avg is not None:
                    subj_w_sum += m_avg * mod_weight
                    subj_w_den += mod_weight

            for eff, w in subj_unlinked_grades.get(subj.id, []):
                subj_w_sum += eff * w
                subj_w_den += w

            s_passing = (
                _q2(
                    sum(subj_passings, Decimal("0.00")) / Decimal(len(subj_passings))
                )
                if subj_passings
                else _DEFAULT_PASSING_SCORE
            )
            s_avg = (
                _q2(subj_w_sum / subj_w_den) if subj_w_den > Decimal("0.00") else None
            )
            s_status, _, s_below = classify_academic_standing(
                s_avg,
                passing_score=s_passing,
                attendance_rate=primary_enrollment.attendance_rate,
            )
            subjects_report.append(
                StudentSubjectAverageSchema(
                    subject_id=subj.id,
                    subject_code=subj.code,
                    subject_name=subj.name,
                    passing_score=s_passing,
                    subject_average=s_avg,
                    is_below_passing_score=s_below,
                    status=s_status,
                    modules=mod_reports,
                )
            )

        # Mapa de competências para Gráfico Radar (inclui competências do curso + evidências avulsas)
        ev_by_comp: dict[UUID, list[Decimal]] = {}
        for ev in skill_evidences:
            ev_by_comp.setdefault(ev.competency_id, []).append(
                Decimal(ev.verified_level)
            )
            if ev.competency_id not in competency_targets:
                competency_targets[ev.competency_id] = (
                    ev.competency.code,
                    ev.competency.title,
                    ev.competency.category,
                    3,
                )

        competencies_radar: list[StudentCompetencyRadarItemSchema] = []
        for comp_id, (c_code, c_title, c_cat, req_lvl) in sorted(
            competency_targets.items(),
            key=lambda kv: kv[1][0],
        ):
            ev_vals = ev_by_comp.get(comp_id, [])
            ver_lvl = (
                _q2(sum(ev_vals, Decimal("0.00")) / Decimal(len(ev_vals)))
                if ev_vals
                else None
            )
            competencies_radar.append(
                StudentCompetencyRadarItemSchema(
                    competency_id=comp_id,
                    code=c_code,
                    title=c_title,
                    category=c_cat,
                    required_level=req_lvl,
                    verified_level=ver_lvl,
                    evidences_count=len(ev_vals),
                    is_proficient=(
                        ver_lvl is not None and ver_lvl >= Decimal(req_lvl)
                    ),
                )
            )

        active_alerts_schemas = [
            StudentActiveAlertItemSchema(
                id=alert.id,
                class_id=alert.class_id,
                module_id=alert.module_id,
                risk_level=alert.risk_level,
                alert_category=alert.alert_category,
                explainable_reason=alert.explainable_reason,
                metric_snapshot=alert.metric_snapshot,
                status=alert.status,
                created_at=alert.created_at,
            )
            for alert in active_alerts_orm
        ]

        return Student360OverviewResponseSchema(
            student_id=student.id,
            student=student_profile,
            enrollment_id=primary_enrollment.id,
            class_id=academic_class.id,
            enrollment_status=primary_enrollment.status,
            academic_class=EnrollmentClassSummarySchema.model_validate(academic_class),
            generated_at=now,
            overview=overview,
            subjects=subjects_report,
            attendance_by_module=attendance_by_module,
            competencies=competencies_radar,
            practical_submissions=practical_submissions_schemas,
            active_alerts=active_alerts_schemas,
        )

    def get_student_portal_dashboard(
        self,
        params: StudentPortalDashboardQueryParams | None = None,
        *,
        current_user: User,
    ) -> StudentPortalDashboardResponseSchema:
        """Retorna o painel privado do estudante autenticado com progresso, frequência, radar e linha do tempo (BE-034).

        - Utiliza exclusivamente current_user.id extraído do token JWT.
        - Nunca consulta ou expõe observações pedagógicas restritas dos professores.
        """
        student = current_user

        requested_class_id = params.class_id if params is not None else None
        if requested_class_id is not None:
            if self._repository.get_class_by_id(requested_class_id) is None:
                raise NotFoundException(message=DASHBOARD_CLASS_NOT_FOUND_MESSAGE)

        enrollments = self._repository.list_student_enrollments(
            student.id,
            class_id=requested_class_id,
        )
        if requested_class_id is not None and not enrollments:
            raise NotFoundException(message=DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE)

        profile = student.profile
        student_profile = DashboardStudentProfileSchema(
            id=student.id,
            email=student.email,
            full_name=profile.full_name if profile is not None else None,
            registration_number=(
                profile.registration_number if profile is not None else None
            ),
            avatar_url=profile.avatar_url if profile is not None else None,
        )
        now = _utc_now()

        if not enrollments:
            empty_att_metrics = compute_attendance_margin_metrics(
                total_hours=0,
                attended_hours=0,
                absent_hours=0,
                planned_hours=0,
            )
            empty_attendance = StudentPortalAttendanceSummarySchema(
                planned_hours=0,
                total_hours=0,
                attended_hours=0,
                absent_hours=0,
                justified_absent_hours=0,
                critical_modules_count=0,
                by_subject=[],
                by_module=[],
                **empty_att_metrics,
            )
            empty_counts = StudentTaskCountsSummarySchema(
                pending_count=0,
                late_count=0,
                completed_count=0,
                submitted_count=0,
                evaluated_count=0,
                total_count=0,
            )
            return StudentPortalDashboardResponseSchema(
                student_id=student.id,
                student=student_profile,
                enrollment_id=None,
                class_id=None,
                enrollment_status=None,
                academic_class=None,
                course_code=None,
                course_name=None,
                generated_at=now,
                overall_average=None,
                overall_progress_percentage=Decimal("0.00"),
                attendance_percentage=Decimal("100.00"),
                standing_status=AcademicStandingStatus.APPROVED,
                risk_level=RiskLevel.LOW,
                overview=None,
                attendance_summary=empty_attendance,
                subjects=[],
                attendance_by_module=[],
                modules_progress=[],
                competencies=[],
                competencies_radar=[],
                task_counts=empty_counts,
                activity_counters=empty_counts,
                upcoming_tasks=[],
                practical_submissions=[],
                timeline=[],
                milestone_history=[],
            )

        primary_enrollment = enrollments[0]
        academic_class = primary_enrollment.academic_class
        course = academic_class.course

        view_360_row = self._repository.query_student_360_view_by_enrollment(
            primary_enrollment.id
        )
        overview = (
            self._map_view_row_to_student_summary(view_360_row)
            if view_360_row is not None
            else None
        )

        # 1. Frequência por módulo e por disciplina via vw_module_attendance_risk (DB-037)
        att_rows = self._repository.query_class_module_attendance_view(
            academic_class.id,
            student_id=student.id,
            exclude_dropped=False,
        )
        attendance_by_module: list[ModuleAttendanceRiskItemSchema] = []
        att_item_by_module_id: dict[UUID, ModuleAttendanceRiskItemSchema] = {}
        mods_att_by_subject: dict[UUID, list[ModuleAttendanceRiskItemSchema]] = {}

        for row in att_rows:
            total_h = int(row["total_hours"] or 0)
            attended_h = int(row["attended_hours"] or 0)
            absent_h = int(row["absent_hours"] or 0)
            justified_h = int(row["justified_absent_hours"] or 0)
            planned_h = int(row["module_planned_hours"] or 0)
            metrics = compute_attendance_margin_metrics(
                total_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                planned_hours=planned_h,
            )
            mod_att_item = ModuleAttendanceRiskItemSchema(
                enrollment_id=UUID(str(row["enrollment_id"])),
                class_id=UUID(str(row["class_id"])),
                class_code=str(row["class_code"]),
                class_period=str(row["class_period"]),
                subject_id=UUID(str(row["subject_id"])),
                subject_code=str(row["subject_code"]),
                subject_name=str(row["subject_name"]),
                module_id=UUID(str(row["module_id"])),
                module_title=str(row["module_title"]),
                order_index=int(row["module_order_index"]),
                planned_hours=planned_h,
                total_hours=total_h,
                attended_hours=attended_h,
                absent_hours=absent_h,
                justified_absent_hours=justified_h,
                **metrics,
            )
            attendance_by_module.append(mod_att_item)
            att_item_by_module_id[mod_att_item.module_id] = mod_att_item
            mods_att_by_subject.setdefault(mod_att_item.subject_id, []).append(
                mod_att_item
            )

        # 2. Carrega disciplinas, avaliações formativas, submissões práticas, evidências e marcos
        subjects = self._repository.list_course_subjects_with_modules_and_competencies(
            academic_class.course_id
        )
        assessments = self._repository.list_class_assessments_with_grades(
            academic_class.id
        )
        detailed_submissions = self._repository.list_student_detailed_submissions(
            student.id,
            class_id=academic_class.id,
        )
        skill_evidences = self._repository.list_skill_evidences_for_students(
            [student.id]
        )
        milestones_orm = self._repository.list_student_milestones(
            student.id,
            enrollment_id=primary_enrollment.id,
        )

        # 3. Consolida resumo de frequência por disciplina e global
        subject_attendance_list: list[SubjectConsolidatedAttendanceSchema] = []
        overall_planned_h = 0
        overall_total_h = 0
        overall_attended_h = 0
        overall_absent_h = 0
        overall_justified_h = 0

        for subj in subjects:
            subj_att_mods = sorted(
                mods_att_by_subject.get(subj.id, []),
                key=lambda item: (item.order_index, item.module_title.lower()),
            )
            s_total_h = sum(m.total_hours for m in subj_att_mods)
            s_attended_h = sum(m.attended_hours for m in subj_att_mods)
            s_absent_h = sum(m.absent_hours for m in subj_att_mods)
            s_justified_h = sum(m.justified_absent_hours for m in subj_att_mods)
            s_planned_h = max(
                int(subj.workload_hours),
                sum(m.planned_hours for m in subj_att_mods),
            )
            s_att_metrics = compute_attendance_margin_metrics(
                total_hours=s_total_h,
                attended_hours=s_attended_h,
                absent_hours=s_absent_h,
                planned_hours=s_planned_h,
            )
            subject_attendance_list.append(
                SubjectConsolidatedAttendanceSchema(
                    enrollment_id=primary_enrollment.id,
                    class_id=academic_class.id,
                    class_code=academic_class.code,
                    class_period=academic_class.period,
                    subject_id=subj.id,
                    subject_code=subj.code,
                    subject_name=subj.name,
                    planned_hours=s_planned_h,
                    total_hours=s_total_h,
                    attended_hours=s_attended_h,
                    absent_hours=s_absent_h,
                    justified_absent_hours=s_justified_h,
                    modules=subj_att_mods,
                    **s_att_metrics,
                )
            )
            overall_planned_h += s_planned_h
            overall_total_h += s_total_h
            overall_attended_h += s_attended_h
            overall_absent_h += s_absent_h
            overall_justified_h += s_justified_h

        if view_360_row is not None and overall_total_h == 0:
            overall_total_h = int(view_360_row.get("total_lesson_hours") or 0)
            overall_attended_h = int(view_360_row.get("attended_hours") or 0)
            overall_absent_h = int(view_360_row.get("absent_hours") or 0)

        overall_att_metrics = compute_attendance_margin_metrics(
            total_hours=overall_total_h,
            attended_hours=overall_attended_h,
            absent_hours=overall_absent_h,
            planned_hours=overall_planned_h,
        )
        if overview is not None and overall_total_h == 0:
            resolved_att_pct = overview.attendance_percentage
        else:
            resolved_att_pct = overall_att_metrics["attendance_percentage"]

        critical_modules_count = sum(
            1 for m_item in attendance_by_module if m_item.is_critical
        )
        attendance_summary = StudentPortalAttendanceSummarySchema(
            planned_hours=overall_planned_h,
            total_hours=overall_total_h,
            attended_hours=overall_attended_h,
            absent_hours=overall_absent_h,
            justified_absent_hours=overall_justified_h,
            attendance_percentage=resolved_att_pct,
            min_required_percentage=overall_att_metrics["min_required_percentage"],
            max_allowed_absent_hours=overall_att_metrics["max_allowed_absent_hours"],
            remaining_absent_hours_margin=overall_att_metrics[
                "remaining_absent_hours_margin"
            ],
            planned_max_allowed_absent_hours=overall_att_metrics[
                "planned_max_allowed_absent_hours"
            ],
            planned_remaining_absent_hours_margin=overall_att_metrics[
                "planned_remaining_absent_hours_margin"
            ],
            percentage_margin_to_limit=overall_att_metrics[
                "percentage_margin_to_limit"
            ],
            is_critical=overall_att_metrics["is_critical"],
            is_attendance_critical=overall_att_metrics["is_attendance_critical"],
            risk_level=overall_att_metrics["risk_level"],
            critical_modules_count=critical_modules_count,
            by_subject=subject_attendance_list,
            by_module=attendance_by_module,
        )

        # 4. Contadores de atividades práticas e agrupamento por módulo
        pending_count = 0
        late_count = 0
        submitted_count = 0
        evaluated_count = 0
        mod_task_scores: dict[UUID, list[Decimal]] = {}
        # Por módulo: [total, completed, pending, late, submitted, evaluated]
        mod_task_counters: dict[UUID, list[int]] = {}
        practical_submissions_schemas: list[StudentPendingTaskItemSchema] = []
        upcoming_tasks_schemas: list[StudentPendingTaskItemSchema] = []

        for sub in detailed_submissions:
            eff_status = PracticalTaskService.resolve_effective_submission_status(
                sub,
                due_date=sub.task.due_date,
                reference_now=now,
            )
            mod_id = sub.task.module_id
            m_cnt = mod_task_counters.setdefault(mod_id, [0, 0, 0, 0, 0, 0])
            m_cnt[0] += 1

            if eff_status == SubmissionStatus.PENDING:
                pending_count += 1
                m_cnt[2] += 1
            elif eff_status == SubmissionStatus.LATE:
                late_count += 1
                m_cnt[3] += 1
            elif eff_status == SubmissionStatus.SUBMITTED:
                submitted_count += 1
                m_cnt[1] += 1
                m_cnt[4] += 1
            elif eff_status == SubmissionStatus.EVALUATED:
                evaluated_count += 1
                m_cnt[1] += 1
                m_cnt[5] += 1

            task_item = PracticalTaskService._to_student_pending_task_item(
                sub,
                effective_status=eff_status,
            )
            practical_submissions_schemas.append(task_item)
            if eff_status in (SubmissionStatus.PENDING, SubmissionStatus.LATE):
                upcoming_tasks_schemas.append(task_item)

            if sub.final_task_score is not None:
                mod_task_scores.setdefault(mod_id, []).append(
                    Decimal(sub.final_task_score)
                )

        completed_count = submitted_count + evaluated_count
        total_tasks_count = pending_count + late_count + completed_count
        task_counts = StudentTaskCountsSummarySchema(
            pending_count=pending_count,
            late_count=late_count,
            completed_count=completed_count,
            submitted_count=submitted_count,
            evaluated_count=evaluated_count,
            total_count=total_tasks_count,
        )

        # 5. Notas formativas por módulo e disciplina
        mod_grades: dict[UUID, list[tuple[Decimal, Decimal]]] = {}
        subj_unlinked_grades: dict[UUID, list[tuple[Decimal, Decimal]]] = {}
        for assessment in assessments:
            w = Decimal(assessment.weight)
            for grade in assessment.grades:
                if grade.student_id != student.id:
                    continue
                eff, _ = compute_senai_effective_grade(
                    grade.grade_value,
                    grade.recovery_grade,
                )
                if assessment.module_id is not None:
                    mod_grades.setdefault(assessment.module_id, []).append((eff, w))
                else:
                    subj_unlinked_grades.setdefault(assessment.subject_id, []).append(
                        (eff, w)
                    )

        # 6. Médias por disciplina, progresso percentual por módulo e alvos de competências
        subjects_report: list[StudentSubjectAverageSchema] = []
        modules_progress: list[StudentModuleProgressItemSchema] = []
        competency_targets: dict[UUID, tuple[str, str, Any, int]] = {}

        for subj in subjects:
            ordered_mods = sorted(
                subj.learning_modules,
                key=lambda m: (m.order_index, m.title.lower(), str(m.id)),
            )
            mod_reports: list[StudentModuleAverageSchema] = []
            subj_w_sum = Decimal("0.00")
            subj_w_den = Decimal("0.00")
            subj_passings: list[Decimal] = []

            for mod in ordered_mods:
                for mc in mod.module_competencies:
                    prev = competency_targets.get(mc.competency_id)
                    req_lvl = (
                        max(prev[3], mc.required_level)
                        if prev is not None
                        else mc.required_level
                    )
                    competency_targets[mc.competency_id] = (
                        mc.competency.code,
                        mc.competency.title,
                        mc.competency.category,
                        req_lvl,
                    )

                mod_passing = _q2(Decimal(mod.passing_score))
                mod_weight = _q2(Decimal(mod.module_weight))
                subj_passings.append(mod_passing)

                g_entries = mod_grades.get(mod.id, [])
                t_scores = mod_task_scores.get(mod.id, [])

                a_num = sum((val * w for val, w in g_entries), Decimal("0.00"))
                a_den = sum((w for _, w in g_entries), Decimal("0.00"))
                a_avg = _q2(a_num / a_den) if a_den > Decimal("0.00") else None

                t_num = sum(
                    (val * _PRACTICAL_TASK_WEIGHT for val in t_scores),
                    Decimal("0.00"),
                )
                t_den = Decimal(len(t_scores)) * _PRACTICAL_TASK_WEIGHT
                t_avg = _q2(t_num / t_den) if t_den > Decimal("0.00") else None

                c_den = a_den + t_den
                m_avg = (
                    _q2((a_num + t_num) / c_den) if c_den > Decimal("0.00") else None
                )

                mod_att_obj = att_item_by_module_id.get(mod.id)
                mod_att_pct = (
                    mod_att_obj.attendance_percentage
                    if mod_att_obj is not None
                    else resolved_att_pct
                )

                m_status, _, m_below = classify_academic_standing(
                    m_avg,
                    passing_score=mod_passing,
                    attendance_rate=mod_att_pct,
                )
                mod_reports.append(
                    StudentModuleAverageSchema(
                        module_id=mod.id,
                        subject_id=subj.id,
                        module_title=mod.title,
                        order_index=mod.order_index,
                        module_weight=mod_weight,
                        passing_score=mod_passing,
                        assessments_count=len(g_entries),
                        practical_tasks_count=len(t_scores),
                        assessments_average=a_avg,
                        practical_tasks_average=t_avg,
                        module_average=m_avg,
                        is_below_passing_score=m_below,
                        status=m_status,
                    )
                )
                if m_avg is not None:
                    subj_w_sum += m_avg * mod_weight
                    subj_w_den += mod_weight

                m_tot, m_comp, m_pend, m_late, m_sub, m_eval = mod_task_counters.get(
                    mod.id,
                    [0, 0, 0, 0, 0, 0],
                )
                if m_tot > 0:
                    mod_prog_pct = _q2(
                        (Decimal(m_comp) * Decimal("100")) / Decimal(m_tot)
                    )
                elif m_avg is not None:
                    mod_prog_pct = Decimal("100.00")
                else:
                    mod_prog_pct = Decimal("0.00")

                modules_progress.append(
                    StudentModuleProgressItemSchema(
                        module_id=mod.id,
                        subject_id=subj.id,
                        subject_code=subj.code,
                        subject_name=subj.name,
                        module_title=mod.title,
                        order_index=mod.order_index,
                        practical_hours=mod.practical_hours,
                        module_weight=mod_weight,
                        passing_score=mod_passing,
                        total_tasks_count=m_tot,
                        completed_tasks_count=m_comp,
                        pending_tasks_count=m_pend,
                        late_tasks_count=m_late,
                        submitted_tasks_count=m_sub,
                        evaluated_tasks_count=m_eval,
                        progress_percentage=mod_prog_pct,
                        completion_percentage=mod_prog_pct,
                        attendance_percentage=mod_att_pct,
                        assessments_count=len(g_entries),
                        assessments_average=a_avg,
                        practical_tasks_average=t_avg,
                        module_average=m_avg,
                        is_below_passing_score=m_below,
                        is_completed=(mod_prog_pct >= Decimal("100.00")),
                        status=m_status,
                    )
                )

            for eff, w in subj_unlinked_grades.get(subj.id, []):
                subj_w_sum += eff * w
                subj_w_den += w

            s_passing = (
                _q2(
                    sum(subj_passings, Decimal("0.00")) / Decimal(len(subj_passings))
                )
                if subj_passings
                else _DEFAULT_PASSING_SCORE
            )
            s_avg = (
                _q2(subj_w_sum / subj_w_den) if subj_w_den > Decimal("0.00") else None
            )
            s_status, _, s_below = classify_academic_standing(
                s_avg,
                passing_score=s_passing,
                attendance_rate=resolved_att_pct,
            )
            subjects_report.append(
                StudentSubjectAverageSchema(
                    subject_id=subj.id,
                    subject_code=subj.code,
                    subject_name=subj.name,
                    passing_score=s_passing,
                    subject_average=s_avg,
                    is_below_passing_score=s_below,
                    status=s_status,
                    modules=mod_reports,
                )
            )

        # 7. Evolução de nível por competência técnica para Gráfico Radar (FE-038)
        ev_by_comp: dict[UUID, list[Decimal]] = {}
        for ev in skill_evidences:
            ev_by_comp.setdefault(ev.competency_id, []).append(
                Decimal(ev.verified_level)
            )
            if ev.competency_id not in competency_targets:
                competency_targets[ev.competency_id] = (
                    ev.competency.code,
                    ev.competency.title,
                    ev.competency.category,
                    3,
                )

        competencies_radar: list[StudentCompetencyRadarItemSchema] = []
        for comp_id, (c_code, c_title, c_cat, req_lvl) in sorted(
            competency_targets.items(),
            key=lambda kv: kv[1][0],
        ):
            ev_vals = ev_by_comp.get(comp_id, [])
            ver_lvl = (
                _q2(sum(ev_vals, Decimal("0.00")) / Decimal(len(ev_vals)))
                if ev_vals
                else None
            )
            competencies_radar.append(
                StudentCompetencyRadarItemSchema(
                    competency_id=comp_id,
                    code=c_code,
                    title=c_title,
                    category=c_cat,
                    required_level=req_lvl,
                    verified_level=ver_lvl,
                    evidences_count=len(ev_vals),
                    is_proficient=(
                        ver_lvl is not None and ver_lvl >= Decimal(req_lvl)
                    ),
                )
            )

        # 8. Linha do tempo acadêmica (student_milestone_history - DB-039 / FE-039)
        timeline_items: list[StudentMilestoneTimelineItemSchema] = []
        for ms in milestones_orm:
            ms_mod = ms.module
            ms_subj = ms_mod.subject if ms_mod is not None else None
            timeline_items.append(
                StudentMilestoneTimelineItemSchema(
                    id=ms.id,
                    student_id=ms.student_id,
                    enrollment_id=ms.enrollment_id,
                    module_id=ms.module_id,
                    module_title=ms_mod.title if ms_mod is not None else None,
                    subject_id=ms_subj.id if ms_subj is not None else None,
                    subject_code=ms_subj.code if ms_subj is not None else None,
                    subject_name=ms_subj.name if ms_subj is not None else None,
                    milestone_type=ms.milestone_type,
                    title=ms.title,
                    description=ms.description,
                    metadata=ms.milestone_metadata,
                    achieved_at=ms.achieved_at,
                )
            )

        if total_tasks_count > 0:
            overall_progress_pct = _q2(
                (Decimal(completed_count) * Decimal("100")) / Decimal(total_tasks_count)
            )
        elif modules_progress:
            overall_progress_pct = _q2(
                sum(
                    (m.progress_percentage for m in modules_progress),
                    Decimal("0.00"),
                )
                / Decimal(len(modules_progress))
            )
        else:
            overall_progress_pct = Decimal("0.00")

        valid_subject_averages = [
            s.subject_average
            for s in subjects_report
            if s.subject_average is not None
        ]
        if valid_subject_averages:
            overall_average: Decimal | None = _q2(
                sum(valid_subject_averages, Decimal("0.00"))
                / Decimal(len(valid_subject_averages))
            )
        else:
            overall_average = (
                overview.overall_average
                if overview is not None
                else primary_enrollment.final_grade
            )
        standing_status, computed_risk, _ = classify_academic_standing(
            overall_average,
            passing_score=_DEFAULT_PASSING_SCORE,
            attendance_rate=resolved_att_pct,
        )
        risk_rank = {
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4,
        }
        view_risk = overview.risk_level if overview is not None else RiskLevel.LOW
        risk_level = (
            view_risk
            if risk_rank[view_risk] >= risk_rank[computed_risk]
            else computed_risk
        )

        return StudentPortalDashboardResponseSchema(
            student_id=student.id,
            student=student_profile,
            enrollment_id=primary_enrollment.id,
            class_id=academic_class.id,
            enrollment_status=primary_enrollment.status,
            academic_class=EnrollmentClassSummarySchema.model_validate(academic_class),
            course_code=course.code if course is not None else None,
            course_name=course.name if course is not None else None,
            generated_at=now,
            overall_average=overall_average,
            overall_progress_percentage=overall_progress_pct,
            attendance_percentage=resolved_att_pct,
            standing_status=standing_status,
            risk_level=risk_level,
            overview=overview,
            attendance_summary=attendance_summary,
            subjects=subjects_report,
            attendance_by_module=attendance_by_module,
            modules_progress=modules_progress,
            competencies=competencies_radar,
            competencies_radar=competencies_radar,
            task_counts=task_counts,
            activity_counters=task_counts,
            upcoming_tasks=upcoming_tasks_schemas,
            practical_submissions=practical_submissions_schemas,
            timeline=timeline_items,
            milestone_history=timeline_items,
        )


def get_dashboard_service(
    repository: DashboardRepositoryDep,
) -> DashboardService:
    """Provedor de injeção de dependência para DashboardService."""
    return DashboardService(repository=repository)


DashboardServiceDep = Annotated[
    DashboardService,
    Depends(get_dashboard_service),
]

__all__ = [
    "DASHBOARD_CLASS_NOT_FOUND_MESSAGE",
    "DASHBOARD_ENROLLMENT_NOT_FOUND_MESSAGE",
    "DASHBOARD_MODULE_NOT_FOUND_MESSAGE",
    "DASHBOARD_STUDENT_NOT_FOUND_MESSAGE",
    "DASHBOARD_SUBJECT_NOT_FOUND_MESSAGE",
    "DASHBOARD_TEACHER_CLASS_FORBIDDEN_MESSAGE",
    "DASHBOARD_TEACHER_STUDENT_FORBIDDEN_MESSAGE",
    "DASHBOARD_TEACHER_SUBJECT_FORBIDDEN_MESSAGE",
    "DashboardService",
    "DashboardServiceDep",
    "get_dashboard_service",
]
