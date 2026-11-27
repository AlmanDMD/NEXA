"""Suíte unitária abrangente para RiskEngineService (BE-032/033/039) e DiagnosticService (BE-037/038) — BE-040."""

from collections.abc import Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import ForbiddenException, NotFoundException
from app.models import (
    AcademicAlert,
    AuditLog,
    Base,
    Enrollment,
    ExplainableDiagnostic,
    ModuleCompetency,
    PracticalTask,
    SelfAssessmentForm,
    SkillEvidence,
    StudentSelfAssessment,
    TaskSubmission,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.competency_repository import CompetencyRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.diagnostic_repository import DiagnosticRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.risk_engine_repository import RiskEngineRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import (
    AlertCategory,
    AlertStatus,
    ClassStatus,
    CompetencyCategory,
    DiagnosticType,
    EnrollmentStatus,
    RiskLevel,
    Shift,
    SubmissionStatus,
    UserRole,
)
from app.schemas.self_assessment import (
    DiagnosticDiscrepanciesQueryParams,
    DiagnosticEvidenceSummarySchema,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.audit_service import AuditService
from app.services.diagnostic_service import (
    ALIGNED_STRICT_THRESHOLD,
    DIAGNOSTIC_CLASS_NOT_FOUND_MESSAGE,
    DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE,
    DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE,
    DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE,
    DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE,
    DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE,
    DISCREPANCY_CRITICAL_THRESHOLD,
    CompetencyDiagnosticInput,
    DiagnosticService,
    _ensure_utc as diag_ensure_utc,
    _q2 as diag_q2,
    _to_dec_or_none as diag_to_dec_or_none,
    evaluate_competency_discrepancy,
    get_diagnostic_service,
    is_safety_or_precision_competency,
)
from app.services.risk_engine_service import (
    DEFAULT_PASSING_SCORE,
    RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE,
    RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE,
    RiskEngineService,
    StudentRiskMetricsInput,
    _q2 as risk_q2,
    _resolve_pedagogical_actions,
    _to_dec_or_none as risk_to_dec_or_none,
    evaluate_student_risk_rules,
    get_risk_engine_service,
    map_alert_audit_logs_to_schema,
)


@pytest.fixture
def unit_session_factory(tmp_path: Path) -> Generator[sessionmaker[Session], None, None]:
    """Cria fábrica de sessões SQLite isolada por teste para exercitar serviços com segurança."""
    db_file = tmp_path / "lote4_services_unit.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _create_user(
    session: Session,
    *,
    role: UserRole,
    suffix: str,
    full_name: str,
) -> User:
    return AuthRepository(session=session).create_user(
        email=f"{role.value.lower()}.{suffix}@senai.br",
        password_hash="$2b$04$dummyhashforunitservice000000000000000000000000000000",
        role=role,
        is_active=True,
        profile_data=UserProfileCreateSchema(
            full_name=full_name,
            registration_number=f"UNIT-{role.value[:3]}-{suffix.upper()}",
            phone="(11) 98888-0000",
        ),
    )


class TestRiskEngineServiceUnitCoverage:
    """Garante cobertura completa das regras puras, helpers e fluxos de serviço do RiskEngineService."""

    def test_decimal_conversion_and_pedagogical_action_resolution_helpers(self) -> None:
        assert risk_q2(Decimal("7.125")) == Decimal("7.13")
        assert risk_to_dec_or_none(None) is None
        assert risk_to_dec_or_none(Decimal("8.5")) == Decimal("8.50")
        assert risk_to_dec_or_none("6.345") == Decimal("6.35")
        assert risk_to_dec_or_none(7) == Decimal("7.00")

        module_stub = SimpleNamespace(title="Metrologia Dimensional")
        alert_custom_snapshot = SimpleNamespace(
            alert_category=AlertCategory.GRADE_DROP,
            metric_snapshot={"recommended_action": "  Reforço individual em paquímetro  "},
            module=module_stub,
        )
        rec, sug = _resolve_pedagogical_actions(alert_custom_snapshot)  # type: ignore[arg-type]
        assert rec == "Reforço individual em paquímetro"
        assert sug == "Agendar mentoria prática no módulo de Metrologia Dimensional."

        alert_att_with_mod = SimpleNamespace(
            alert_category=AlertCategory.ATTENDANCE,
            metric_snapshot=None,
            module=module_stub,
        )
        rec_att, sug_att = _resolve_pedagogical_actions(alert_att_with_mod)  # type: ignore[arg-type]
        assert "acolhimento pedagógico" in rec_att.lower()
        assert "Metrologia Dimensional" in sug_att

        alert_generic = SimpleNamespace(
            alert_category=AlertCategory.SELF_EVAL_GAP,
            metric_snapshot={"recommended_action": "   "},
            module=None,
        )
        rec_gen, sug_gen = _resolve_pedagogical_actions(alert_generic)  # type: ignore[arg-type]
        assert "devolutiva individual" in rec_gen.lower()
        assert "devolutiva individual" in sug_gen.lower()

    def test_map_alert_audit_logs_handles_invalid_statuses_and_missing_profiles(self) -> None:
        now = datetime.now(timezone.utc)
        user_with_profile = SimpleNamespace(
            role=UserRole.TEACHER,
            email="prof.p@senai.br",
            profile=SimpleNamespace(full_name="Prof. Com Perfil"),
        )
        user_without_profile = SimpleNamespace(
            role=UserRole.COORDINATOR,
            email="coord.noprofile@senai.br",
            profile=None,
        )

        logs = [
            SimpleNamespace(
                id=uuid4(),
                user_id=uuid4(),
                action="ACADEMIC_ALERT_ACKNOWLEDGED",
                old_values={"status": "ACTIVE"},
                new_values={"status": "ACKNOWLEDGED", "resolution_notes": "Acolhimento feito."},
                user=user_with_profile,
                ip_address="127.0.0.1",
                created_at=now,
            ),
            SimpleNamespace(
                id=uuid4(),
                user_id=uuid4(),
                action="ACADEMIC_ALERT_RESOLVED",
                old_values={"status": "INVALID_PREV"},
                new_values={"status": "INVALID_NEW", "resolution_notes": "Resolvido."},
                user=user_without_profile,
                ip_address=None,
                created_at=now,
            ),
            SimpleNamespace(
                id=uuid4(),
                user_id=uuid4(),
                action="ACADEMIC_ALERT_RESOLVED",
                old_values=None,
                new_values=None,
                user=None,
                ip_address=None,
                created_at=now,
            ),
        ]

        mapped = map_alert_audit_logs_to_schema(logs)  # type: ignore[arg-type]
        assert len(mapped) == 3
        assert mapped[0].previous_status == AlertStatus.ACTIVE
        assert mapped[0].new_status == AlertStatus.ACKNOWLEDGED
        assert mapped[0].actor_name == "Prof. Com Perfil"

        assert mapped[1].previous_status is None
        assert mapped[1].new_status == AlertStatus.RESOLVED
        assert mapped[1].actor_name == "coord.noprofile@senai.br"

        assert mapped[2].previous_status is None
        assert mapped[2].new_status == AlertStatus.RESOLVED
        assert mapped[2].actor_name is None
        assert mapped[2].actor_role is None

    def test_evaluate_student_risk_rules_all_boundaries(self) -> None:
        # 1. LOW com overall_average None
        lvl_none, rules_none = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("78.00"),
                late_tasks_count=1,
                overall_average=None,
                passing_score=Decimal("6.00"),
            )
        )
        assert lvl_none == RiskLevel.LOW
        assert rules_none == []

        # 2. MODERATE (exatamente 2 tarefas atrasadas)
        lvl_mod, rules_mod = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("95.00"),
                late_tasks_count=2,
                total_tasks_count=4,
                overall_average=Decimal("6.00"),
                passing_score=Decimal("6.00"),
            )
        )
        assert lvl_mod == RiskLevel.MODERATE
        assert rules_mod[0].rule_code == "PRACTICAL_TASKS_LATE_MODERATE"

        # 3. HIGH (faixa preventiva 75.00..77.99 + >= 3 atrasos + média abaixo de corte)
        lvl_high, rules_high = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("76.00"),
                late_tasks_count=4,
                total_tasks_count=5,
                overall_average=Decimal("5.50"),
                passing_score=Decimal("6.00"),
            )
        )
        assert lvl_high == RiskLevel.HIGH
        assert {r.rule_code for r in rules_high} == {
            "ATTENDANCE_PREVENTIVE_75_TO_78",
            "PRACTICAL_TASKS_LATE_HIGH",
            "PARTIAL_AVERAGE_BELOW_PASSING_SCORE",
        }

        # 4. CRITICAL (< 75.00%)
        lvl_crit, rules_crit = evaluate_student_risk_rules(
            StudentRiskMetricsInput(
                attendance_percentage=Decimal("74.99"),
                absent_hours=10,
                total_lesson_hours=40,
                late_tasks_count=0,
                overall_average=Decimal("8.00"),
            )
        )
        assert lvl_crit == RiskLevel.CRITICAL
        assert rules_crit[0].rule_code == "ATTENDANCE_CRITICAL_BELOW_75"

    def test_risk_engine_service_edge_cases_dedup_external_alerts_and_di(
        self,
        unit_session_factory: sessionmaker[Session],
    ) -> None:
        with unit_session_factory() as session:
            teacher = _create_user(session, role=UserRole.TEACHER, suffix="r1", full_name="Prof R1")
            other_teacher = _create_user(session, role=UserRole.TEACHER, suffix="r2", full_name="Prof R2")
            stu_1 = _create_user(session, role=UserRole.STUDENT, suffix="rs1", full_name="Aluno R1")

            course_no_mod = CourseRepository(session).create(
                code="CRS-NOMOD-01",
                name="Curso Sem Módulos",
                description="Teste sem módulos",
                total_hours=200,
                is_active=True,
            )
            class_empty = AcademicClassRepository(session).create(
                course_id=course_no_mod.id,
                code="TURMA-VAZIA-01",
                period="2026.1",
                shift=Shift.MORNING,
                max_students=20,
                status=ClassStatus.ACTIVE,
                start_date=date(2026, 2, 1),
                end_date=date(2026, 12, 31),
            )
            subject = SubjectRepository(session).create(
                course_id=course_no_mod.id,
                code="SUBJ-R1",
                name="Disciplina Teste R1",
                workload_hours=60,
                is_active=True,
            )
            session.add(
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=class_empty.id,
                    subject_id=subject.id,
                )
            )
            enr = Enrollment(
                student_id=stu_1.id,
                class_id=class_empty.id,
                status=EnrollmentStatus.ACTIVE,
                attendance_rate=Decimal("70.00"),
            )
            session.add(enr)
            session.flush()

            # Cria 2 alertas ATTENDANCE duplicados legados + 1 alerta externo SELF_EVAL_GAP CRITICAL
            dup1 = AcademicAlert(
                student_id=stu_1.id,
                enrollment_id=enr.id,
                class_id=class_empty.id,
                risk_level=RiskLevel.HIGH,
                alert_category=AlertCategory.ATTENDANCE,
                explainable_reason="Alerta legado 1 de frequência.",
                status=AlertStatus.ACTIVE,
            )
            dup2 = AcademicAlert(
                student_id=stu_1.id,
                enrollment_id=enr.id,
                class_id=class_empty.id,
                risk_level=RiskLevel.HIGH,
                alert_category=AlertCategory.ATTENDANCE,
                explainable_reason="Alerta legado 2 duplicado de frequência.",
                status=AlertStatus.ACTIVE,
            )
            ext_gap = AcademicAlert(
                student_id=stu_1.id,
                enrollment_id=enr.id,
                class_id=class_empty.id,
                risk_level=RiskLevel.CRITICAL,
                alert_category=AlertCategory.SELF_EVAL_GAP,
                explainable_reason="Discrepância crítica de autoavaliação em NR-12.",
                status=AlertStatus.ACTIVE,
            )
            session.add_all([dup1, dup2, ext_gap])
            session.commit()

            repo = RiskEngineRepository(session=session)
            service = get_risk_engine_service(
                repository=repo,
                audit_service=AuditService(repository=repo._session and __import__("app.repositories.audit_repository", fromlist=["AuditRepository"]).AuditRepository(session=session)),
            )
            assert isinstance(service, RiskEngineService)

            # Curso sem módulos retorna DEFAULT_PASSING_SCORE
            assert service._resolve_course_passing_score(course_no_mod.id) == DEFAULT_PASSING_SCORE

            # Turma inexistente / matrícula inexistente retornam [] / None
            assert service.evaluate_class_students_risk(class_id=uuid4()) == []
            assert service.evaluate_student_enrollment_risk(enrollment_id=uuid4()) is None

            # Turma vazia sem matrículas retorna []
            class_zero = AcademicClassRepository(session).create(
                course_id=course_no_mod.id,
                code="TURMA-ZERO-02",
                period="2026.1",
                shift=Shift.NIGHT,
                max_students=20,
                status=ClassStatus.ACTIVE,
                start_date=date(2026, 2, 1),
                end_date=date(2026, 12, 31),
            )
            assert service.evaluate_class_students_risk(class_id=class_zero.id) == []

            # Verifica exceções em evaluate_class_risk (404 / 403)
            with pytest.raises(NotFoundException, match=RISK_ENGINE_CLASS_NOT_FOUND_MESSAGE):
                service.evaluate_class_risk(uuid4(), current_user=teacher)
            with pytest.raises(ForbiddenException, match=RISK_ENGINE_TEACHER_FORBIDDEN_MESSAGE):
                service.evaluate_class_risk(class_empty.id, current_user=other_teacher)

            # Na view vw_student_360_performance, sem aulas registradas prevalece attendance_rate=70.00% da matrícula (< 75%),
            # logo dup1 é atualizado (updated=1), dup2 é consolidado (auto_resolved=1) e ext_gap (SELF_EVAL_GAP CRITICAL) é preservado.
            single_res = service.evaluate_student_enrollment_risk(enrollment_id=enr.id)
            assert single_res is not None
            assert single_res.updated_alerts_count == 1
            assert single_res.auto_resolved_alerts_count == 1
            assert single_res.overall_risk_level == RiskLevel.CRITICAL
            assert {a.alert_category for a in single_res.active_alerts} == {
                AlertCategory.ATTENDANCE,
                AlertCategory.SELF_EVAL_GAP,
            }

            # Quando a frequência normaliza para 90.00%, o alerta ATTENDANCE restante é auto-resolvido
            # enquanto o alerta externo SELF_EVAL_GAP CRITICAL continua preservado elevando overall_risk_level!
            normalized_res = service._evaluate_and_sync_rows(
                class_id=class_empty.id,
                passing_score=Decimal("6.00"),
                view_rows=[
                    {
                        "enrollment_id": enr.id,
                        "student_id": stu_1.id,
                        "attendance_percentage": Decimal("90.00"),
                        "overall_average": Decimal("8.00"),
                        "total_lesson_hours": 20,
                        "attended_hours": 18,
                        "absent_hours": 2,
                        "late_tasks_count": 0,
                        "pending_tasks_count": 0,
                        "completed_tasks_count": 2,
                        "total_tasks_count": 2,
                    }
                ],
                evaluated_at=datetime.now(timezone.utc),
            )
            assert normalized_res[0].auto_resolved_alerts_count == 1
            assert normalized_res[0].overall_risk_level == RiskLevel.CRITICAL
            assert len(normalized_res[0].active_alerts) == 1
            assert normalized_res[0].active_alerts[0].alert_category == AlertCategory.SELF_EVAL_GAP

            # Testa também consolidação de duplicatas quando a regra dispara (usando _evaluate_and_sync_rows)
            dup_a = AcademicAlert(
                student_id=stu_1.id,
                enrollment_id=enr.id,
                class_id=class_empty.id,
                risk_level=RiskLevel.MODERATE,
                alert_category=AlertCategory.PENDING_TASKS,
                explainable_reason="Duplicado A de tarefa atrasada.",
                status=AlertStatus.ACTIVE,
            )
            dup_b = AcademicAlert(
                student_id=stu_1.id,
                enrollment_id=enr.id,
                class_id=class_empty.id,
                risk_level=RiskLevel.MODERATE,
                alert_category=AlertCategory.PENDING_TASKS,
                explainable_reason="Duplicado B de tarefa atrasada.",
                status=AlertStatus.ACTIVE,
            )
            session.add_all([dup_a, dup_b])
            session.commit()

            rows_res = service._evaluate_and_sync_rows(
                class_id=class_empty.id,
                passing_score=Decimal("6.00"),
                view_rows=[
                    {
                        "enrollment_id": enr.id,
                        "student_id": stu_1.id,
                        "attendance_percentage": Decimal("90.00"),
                        "overall_average": Decimal("8.00"),
                        "total_lesson_hours": 20,
                        "attended_hours": 18,
                        "absent_hours": 2,
                        "late_tasks_count": 3,
                        "pending_tasks_count": 0,
                        "completed_tasks_count": 2,
                        "total_tasks_count": 5,
                    }
                ],
                evaluated_at=datetime.now(timezone.utc),
            )
            assert rows_res[0].updated_alerts_count == 1
            assert rows_res[0].auto_resolved_alerts_count == 1

            # Curso com módulos calcula a média da passing_score
            LearningModuleRepository(session).create(
                subject_id=subject.id,
                title="Módulo A",
                order_index=1,
                practical_hours=20,
                module_weight=Decimal("1.00"),
                passing_score=Decimal("7.00"),
            )
            LearningModuleRepository(session).create(
                subject_id=subject.id,
                title="Módulo B",
                order_index=2,
                practical_hours=20,
                module_weight=Decimal("1.00"),
                passing_score=Decimal("6.00"),
            )
            assert service._resolve_course_passing_score(course_no_mod.id) == Decimal("6.50")


class TestDiagnosticServiceUnitCoverage:
    """Garante cobertura completa do algoritmo de cruzamento diagnóstico e fluxos de serviço do DiagnosticService."""

    def test_helpers_and_safety_precision_classification(self) -> None:
        assert diag_q2(Decimal("2.345")) == Decimal("2.35")
        naive_dt = datetime(2026, 5, 1, 10, 0, 0)
        aware_dt = datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc)
        assert diag_ensure_utc(naive_dt).tzinfo == timezone.utc
        assert diag_ensure_utc(aware_dt).tzinfo == timezone.utc

        assert diag_to_dec_or_none(None) is None
        assert diag_to_dec_or_none(Decimal("4.5")) == Decimal("4.50")
        assert diag_to_dec_or_none("3.124") == Decimal("3.12")

        assert is_safety_or_precision_competency(category=CompetencyCategory.SAFETY) is True
        assert is_safety_or_precision_competency(category=CompetencyCategory.TECHNICAL) is True
        assert is_safety_or_precision_competency(category=CompetencyCategory.PROCEDURAL) is True
        other_category = SimpleNamespace(value="OTHER")
        assert (
            is_safety_or_precision_competency(
                category=other_category,  # type: ignore[arg-type]
                code="COMP-OTH-01",
                title="Uso de Micrômetro e Segurança NR-12",
            )
            is True
        )
        assert (
            is_safety_or_precision_competency(
                category=other_category,  # type: ignore[arg-type]
                code="COMP-OTH-02",
                title="Trabalho em Equipe e Organização",
            )
            is False
        )

    def test_evaluate_competency_discrepancy_all_branches(self) -> None:
        comp_id = uuid4()
        now = datetime.now(timezone.utc)
        ev = DiagnosticEvidenceSummarySchema(
            evidence_id=uuid4(),
            competency_id=comp_id,
            source_submission_id=uuid4(),
            task_id=uuid4(),
            task_title="Peça H7",
            verified_level=Decimal("3.00"),
            verified_by=uuid4(),
            recorded_at=now,
        )

        # INSUFFICIENT_EVIDENCE com perceived_level <= 2 vs > 2
        ins_low = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C1",
                competency_title="Leitura",
                competency_category=CompetencyCategory.TECHNICAL,
                module_title="Metrologia",
                perceived_level=2,
                evidence_count=0,
                avg_verified_level=None,
            )
        )
        assert ins_low.diagnostic_type == DiagnosticType.INSUFFICIENT_EVIDENCE
        assert "acompanhamento preventivo em bancada" in ins_low.recommended_action

        ins_high = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C1",
                competency_title="Leitura",
                competency_category=CompetencyCategory.TECHNICAL,
                module_title="Metrologia",
                perceived_level=4,
                evidence_count=0,
                avg_verified_level=None,
            )
        )
        assert "Aguardar o registro e avaliação" in ins_high.recommended_action

        # OVERCONFIDENCE_RISK: TECHNICAL com 1.50 <= gap < 2.00 -> HIGH
        over_high = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C2",
                competency_title="Paquímetro",
                competency_category=CompetencyCategory.TECHNICAL,
                module_title="Metrologia",
                perceived_level=4,
                avg_verified_level=Decimal("2.50"),
                evidence_count=1,
                evidences_used=[ev],
            )
        )
        assert over_high.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
        assert over_high.discrepancy_gap == DISCREPANCY_CRITICAL_THRESHOLD
        assert over_high.should_trigger_pedagogical_alert is True
        assert over_high.alert_risk_level == RiskLevel.HIGH

        # OVERCONFIDENCE_RISK: categoria não-crítica sem palavras-chave -> não dispara alerta
        over_other = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C3",
                competency_title="Comunicação Assertiva",
                competency_category=SimpleNamespace(value="OTHER"),  # type: ignore[arg-type]
                module_title="Gestão",
                perceived_level=5,
                avg_verified_level=Decimal("2.00"),
                evidence_count=1,
            )
        )
        assert over_other.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
        assert over_other.should_trigger_pedagogical_alert is False

        # ALIGNED estrito com nível inicial (<= 2.00), ALIGNED moderado (0.80 < |gap| < 1.50), e ALIGNED estrito regular
        al_init = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C4",
                competency_title="Ajuste Fino",
                competency_category=CompetencyCategory.PROCEDURAL,
                module_title="Tornearia",
                perceived_level=2,
                avg_verified_level=Decimal("2.00"),
                evidence_count=1,
            )
        )
        assert al_init.diagnostic_type == DiagnosticType.ALIGNED
        assert al_init.is_strictly_aligned is True
        assert "nível inicial" in al_init.recommended_action

        al_mod = evaluate_competency_discrepancy(
            CompetencyDiagnosticInput(
                competency_id=comp_id,
                competency_code="C4",
                competency_title="Ajuste Fino",
                competency_category=CompetencyCategory.PROCEDURAL,
                module_title="Tornearia",
                perceived_level=4,
                avg_verified_level=Decimal("3.00"),
                evidence_count=1,
            )
        )
        assert al_mod.diagnostic_type == DiagnosticType.ALIGNED
        assert al_mod.abs_discrepancy > ALIGNED_STRICT_THRESHOLD
        assert al_mod.is_strictly_aligned is False
        assert "calibração" in al_mod.recommended_action

    def test_diagnostic_service_dedup_auto_sync_and_rbac_branches(
        self,
        unit_session_factory: sessionmaker[Session],
    ) -> None:
        now = datetime.now(timezone.utc)
        with unit_session_factory() as session:
            teacher = _create_user(session, role=UserRole.TEACHER, suffix="d1", full_name="Prof D1")
            teacher_no_class = _create_user(session, role=UserRole.TEACHER, suffix="d2", full_name="Prof Sem Turma")
            student_1 = _create_user(session, role=UserRole.STUDENT, suffix="ds1", full_name="Aluno D1")
            student_2 = _create_user(session, role=UserRole.STUDENT, suffix="ds2", full_name="Aluno D2")

            course = CourseRepository(session).create(
                code="TEC-DIAG-U1",
                name="Técnico em Mecânica",
                description="Curso",
                total_hours=1200,
                is_active=True,
            )
            klass = AcademicClassRepository(session).create(
                course_id=course.id,
                code="MEC-DIAG-U1",
                period="2026.1",
                shift=Shift.MORNING,
                max_students=30,
                status=ClassStatus.ACTIVE,
                start_date=date(2026, 2, 1),
                end_date=date(2026, 12, 31),
            )
            other_klass = AcademicClassRepository(session).create(
                course_id=course.id,
                code="MEC-DIAG-U2",
                period="2026.1",
                shift=Shift.NIGHT,
                max_students=30,
                status=ClassStatus.ACTIVE,
                start_date=date(2026, 2, 1),
                end_date=date(2026, 12, 31),
            )
            subject = SubjectRepository(session).create(
                course_id=course.id,
                code="MET-U1",
                name="Metrologia",
                workload_hours=80,
                is_active=True,
            )
            module = LearningModuleRepository(session).create(
                subject_id=subject.id,
                title="Módulo Único",
                order_index=1,
                practical_hours=40,
                module_weight=Decimal("1.00"),
                passing_score=Decimal("6.00"),
            )
            comp = CompetencyRepository(session).create(
                code="COMP-U1",
                title="Segurança NR-12",
                category=CompetencyCategory.SAFETY,
            )
            session.add(ModuleCompetency(module_id=module.id, competency_id=comp.id, weight=Decimal("1.00"), required_level=4))
            session.add(TeacherAssignment(teacher_id=teacher.id, class_id=klass.id, subject_id=subject.id))
            enr1 = Enrollment(student_id=student_1.id, class_id=klass.id, status=EnrollmentStatus.ACTIVE)
            session.add(enr1)
            session.flush()

            task = PracticalTask(
                module_id=module.id,
                class_id=klass.id,
                title="Tarefa Prática U1",
                due_date=now + timedelta(days=3),
                max_score=Decimal("10.00"),
            )
            session.add(task)
            session.flush()
            sub = TaskSubmission(
                task_id=task.id,
                student_id=student_1.id,
                enrollment_id=enr1.id,
                status=SubmissionStatus.EVALUATED,
                final_task_score=Decimal("4.00"),
            )
            session.add(sub)
            session.flush()
            session.add(
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp.id,
                    source_submission_id=sub.id,
                    verified_level=Decimal("2.00"),
                    verified_by=teacher.id,
                )
            )
            form = SelfAssessmentForm(
                module_id=module.id,
                class_id=klass.id,
                title="Autoavaliação U1",
                opens_at=now - timedelta(days=1),
                closes_at=now + timedelta(days=5),
                is_active=True,
                created_by=teacher.id,
            )
            session.add(form)
            session.flush()
            session.add(
                StudentSelfAssessment(
                    form_id=form.id,
                    student_id=student_1.id,
                    competency_id=comp.id,
                    perceived_level=5,
                    confidence_score=5,
                )
            )
            session.commit()

            service = get_diagnostic_service(repository=DiagnosticRepository(session=session))
            assert isinstance(service, DiagnosticService)

            # 1. Docente sem turmas atribuídas recebe resposta vazia sem erro
            empty_teacher_res = service.get_discrepancies(
                DiagnosticDiscrepanciesQueryParams(),
                current_user=teacher_no_class,
            )
            assert empty_teacher_res.total == 0
            assert empty_teacher_res.discrepancies == []

            # 2. Valida 403 e 404 nos fluxos de evaluate_class_diagnostics e get_discrepancies
            with pytest.raises(NotFoundException, match=DIAGNOSTIC_CLASS_NOT_FOUND_MESSAGE):
                service.evaluate_class_diagnostics(uuid4(), current_user=teacher)
            with pytest.raises(NotFoundException, match=DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE):
                service.evaluate_class_diagnostics(klass.id, module_id=uuid4(), current_user=teacher)
            with pytest.raises(ForbiddenException, match=DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE):
                service.evaluate_class_diagnostics(klass.id, current_user=teacher_no_class)

            with pytest.raises(ForbiddenException, match=DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE):
                service.get_discrepancies(
                    DiagnosticDiscrepanciesQueryParams(student_id=student_2.id),
                    current_user=student_1,
                )
            with pytest.raises(ForbiddenException, match=DIAGNOSTIC_STUDENT_NOT_ENROLLED_MESSAGE):
                service.get_discrepancies(
                    DiagnosticDiscrepanciesQueryParams(class_id=other_klass.id),
                    current_user=student_1,
                )
            with pytest.raises(ForbiddenException, match=DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE):
                service.get_discrepancies(
                    DiagnosticDiscrepanciesQueryParams(class_id=klass.id, student_id=student_2.id),
                    current_user=teacher,
                )
            with pytest.raises(ForbiddenException, match=DIAGNOSTIC_TEACHER_STUDENT_FORBIDDEN_MESSAGE):
                service.get_discrepancies(
                    DiagnosticDiscrepanciesQueryParams(student_id=student_2.id),
                    current_user=teacher,
                )
            with pytest.raises(NotFoundException, match=DIAGNOSTIC_MODULE_NOT_FOUND_MESSAGE):
                service.get_discrepancies(
                    DiagnosticDiscrepanciesQueryParams(module_id=uuid4()),
                    current_user=teacher,
                )

            # 3. Auto-sincronização em get_discrepancies sem class_id (descobre distinct_cids na view)
            auto_synced = service.get_discrepancies(
                DiagnosticDiscrepanciesQueryParams(student_id=student_1.id),
                current_user=teacher,
            )
            assert auto_synced.total == 1
            assert auto_synced.discrepancies[0].diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
            assert auto_synced.discrepancies[0].pedagogical_alert_triggered is True

            # 4. Cria segunda evidência nivel 5 (média passa a (2+5)/2 = 3.50; gap 5-3.50 = 1.50 ainda crítico)
            # e outra nivel 5 (média 4.00; gap = 1.00 < 1.50 -> ALIGNED e auto-resolve alerta SELF_EVAL_GAP!)
            session.add(
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp.id,
                    source_submission_id=sub.id,
                    verified_level=Decimal("5.00"),
                    verified_by=teacher.id,
                )
            )
            session.add(
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp.id,
                    source_submission_id=sub.id,
                    verified_level=Decimal("5.00"),
                    verified_by=teacher.id,
                )
            )
            session.commit()

            re_eval = service.evaluate_class_diagnostics(klass.id, current_user=teacher)
            assert re_eval.aligned_count == 1
            assert re_eval.pedagogical_alerts_triggered_count == 0
            resolved_alert = session.scalar(
                select(AcademicAlert).where(
                    AcademicAlert.student_id == student_1.id,
                    AcademicAlert.alert_category == AlertCategory.SELF_EVAL_GAP,
                )
            )
            assert resolved_alert is not None
            assert resolved_alert.status == AlertStatus.RESOLVED

            # 5. View sem resultados retorna lista vazia
            assert service.run_diagnostic_crossover(class_id=other_klass.id) == []
