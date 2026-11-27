"""Testes unitários e de integração para o Motor de Cruzamento Diagnóstico: Autoavaliação vs. Avaliação Prática do Docente (BE-037)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    AcademicAlert,
    Base,
    Enrollment,
    ExplainableDiagnostic,
    ModuleCompetency,
    PracticalTask,
    SelfAssessmentForm,
    SkillEvidence,
    StudentSelfAssessment,
    TaskCriterion,
    TaskSubmission,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.competency_repository import CompetencyRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
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
from app.schemas.self_assessment import DiagnosticEvidenceSummarySchema
from app.schemas.user import UserProfileCreateSchema
from app.services.diagnostic_service import (
    CompetencyDiagnosticInput,
    DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE,
    SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
    evaluate_competency_discrepancy,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL e views analíticas."""
    db_file = tmp_path / "diagnostic_service_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_pragma(
        dbapi_connection: Any,
        _connection_record: Any,
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: sa.Engine) -> sessionmaker[Session]:
    """Fábrica de sessões SQLAlchemy vinculada à engine isolada."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Hasher rápido para testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def diagnostic_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância FastAPI configurada com banco isolado."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher
    return application


@pytest.fixture
async def client(diagnostic_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=diagnostic_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as http_client:
        yield http_client


def _seed_user_with_token(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    *,
    email: str,
    role: UserRole,
    full_name: str,
    registration_number: str,
) -> tuple[User, str]:
    with db_session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=email,
            password_hash=fast_hasher.hash_password("Senai@123"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=full_name,
                registration_number=registration_number,
                phone="(11) 98888-7777",
            ),
        )
        token = create_access_token(
            subject=user.id,
            email=user.email,
            role=user.role,
        )
        return user, token


def test_evaluate_competency_discrepancy_all_four_scenarios_unit() -> None:
    """DoD e Critérios 1, 2 e 3: Testa unitariamente os 4 cenários (ALIGNED, OVERCONFIDENCE_RISK, UNDERCONFIDENCE_SUPPORT, INSUFFICIENT_EVIDENCE)."""
    now = datetime(2026, 5, 15, 14, 0, tzinfo=timezone.utc)
    comp_id = uuid4()
    ev_summary = DiagnosticEvidenceSummarySchema(
        evidence_id=uuid4(),
        competency_id=comp_id,
        source_submission_id=uuid4(),
        task_id=uuid4(),
        task_title="Usinagem de Eixo H7 no Torno",
        verified_level=Decimal("3.50"),
        verified_by=uuid4(),
        recorded_at=now,
    )

    # Cenário 1: |perceived - verified| <= 0.8 -> ALIGNED (ex: 4.00 vs 3.50 -> gap +0.50)
    res_aligned = evaluate_competency_discrepancy(
        CompetencyDiagnosticInput(
            competency_id=comp_id,
            competency_code="COMP-MET-01",
            competency_title="Medição com Micrômetro Centesimal",
            competency_category=CompetencyCategory.TECHNICAL,
            module_title="Metrologia Aplicada",
            perceived_level=4,
            confidence_score=4,
            avg_verified_level=Decimal("3.50"),
            evidence_count=1,
            evidences_used=[ev_summary],
        )
    )
    assert res_aligned.diagnostic_type == DiagnosticType.ALIGNED
    assert res_aligned.is_strictly_aligned is True
    assert res_aligned.discrepancy_gap == Decimal("0.50")
    assert res_aligned.should_trigger_pedagogical_alert is False
    assert "Usinagem de Eixo H7 no Torno" in res_aligned.explanation_text
    assert SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER in res_aligned.limitations_note

    # Cenário 2: perceived - verified >= 1.5 -> OVERCONFIDENCE_RISK (ex: 5.00 vs 2.50 -> gap +2.50 em SAFETY -> alerta CRITICAL)
    res_overconf = evaluate_competency_discrepancy(
        CompetencyDiagnosticInput(
            competency_id=comp_id,
            competency_code="COMP-SEG-01",
            competency_title="Bloqueio e Proteção NR-12 em Torno Mecânico",
            competency_category=CompetencyCategory.SAFETY,
            module_title="Tornearia Convencional",
            perceived_level=5,
            confidence_score=5,
            avg_verified_level=Decimal("2.50"),
            evidence_count=1,
            evidences_used=[ev_summary],
        )
    )
    assert res_overconf.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
    assert res_overconf.discrepancy_gap == Decimal("2.50")
    assert res_overconf.should_trigger_pedagogical_alert is True
    assert res_overconf.alert_risk_level == RiskLevel.CRITICAL
    assert res_overconf.alert_explainable_reason is not None
    assert "segurança operacional" in res_overconf.alert_explainable_reason
    assert SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER in res_overconf.limitations_note

    # Cenário 3: verified - perceived >= 1.5 -> UNDERCONFIDENCE_SUPPORT (ex: 2.00 vs 4.20 -> gap -2.20)
    res_underconf = evaluate_competency_discrepancy(
        CompetencyDiagnosticInput(
            competency_id=comp_id,
            competency_code="COMP-TOR-02",
            competency_title="Rosqueamento Métrico Interno",
            competency_category=CompetencyCategory.PROCEDURAL,
            module_title="Tornearia Convencional",
            perceived_level=2,
            confidence_score=2,
            avg_verified_level=Decimal("4.20"),
            evidence_count=2,
            difficulty_notes="Receio de quebrar a ferramenta no fundo da rosca.",
            evidences_used=[ev_summary],
        )
    )
    assert res_underconf.diagnostic_type == DiagnosticType.UNDERCONFIDENCE_SUPPORT
    assert res_underconf.discrepancy_gap == Decimal("-2.20")
    assert res_underconf.should_trigger_pedagogical_alert is False
    assert "Receio de quebrar a ferramenta" in res_underconf.limitations_note
    assert SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER in res_underconf.limitations_note

    # Cenário 4: Sem entregas avaliadas (evidence_count == 0) -> INSUFFICIENT_EVIDENCE
    res_insufficient = evaluate_competency_discrepancy(
        CompetencyDiagnosticInput(
            competency_id=comp_id,
            competency_code="COMP-TOR-03",
            competency_title="Torneamento Cônico com Carro Superior",
            competency_category=CompetencyCategory.TECHNICAL,
            module_title="Tornearia Convencional",
            perceived_level=3,
            confidence_score=3,
            avg_verified_level=None,
            evidence_count=0,
            evidences_used=[],
        )
    )
    assert res_insufficient.diagnostic_type == DiagnosticType.INSUFFICIENT_EVIDENCE
    assert res_insufficient.evidence_count == 0
    assert res_insufficient.discrepancy_gap == Decimal("0.00")
    assert res_insufficient.should_trigger_pedagogical_alert is False
    assert (
        SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER
        in res_insufficient.limitations_note
    )


@pytest.mark.asyncio
async def test_diagnostic_service_queries_view_persists_all_4_scenarios_and_generates_pedagogical_alerts(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida a integração completa do DiagnosticService com vw_self_eval_discrepancy, explainable_diagnostics, academic_alerts e BE-025."""
    teacher, teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.diagnostico@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Diagnóstico SENAI",
        registration_number="PROF-2026-0371",
    )
    other_teacher, other_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.externo@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Externo",
        registration_number="PROF-2026-0372",
    )
    student, student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.diagnostico@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Diagnóstico Explicável",
        registration_number="ALU-2026-0371",
    )

    now = datetime.now(timezone.utc)

    with db_session_factory() as session:
        course = CourseRepository(session=session).create(
            name="Técnico em Mecânica Industrial",
            code="TEC-MEC-037",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session=session).create(
            course_id=course.id,
            code="MEC-2026-037",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 15),
        )
        subject = SubjectRepository(session=session).create(
            course_id=course.id,
            name="Usinagem e Metrologia de Precisão",
            code="USI-MET-037",
            workload_hours=100,
            is_active=True,
        )
        module = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 1: Tornearia e Controle Dimensional",
            order_index=1,
            description="Operação de torno e medição centesimal.",
            practical_hours=50,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )

        comp_repo = CompetencyRepository(session=session)
        # 1. Competência para cenário ALIGNED (|4 - 3.50| = 0.50 <= 0.80)
        comp_aligned = comp_repo.create(
            code="COMP-ALI-01",
            title="Faceamento e Escalonamento Linear",
            category=CompetencyCategory.PROCEDURAL,
            description="Executar faceamento perpendicular ao eixo.",
        )
        # 2. Competência de Segurança para cenário OVERCONFIDENCE_RISK (5 - 2.00 = +3.00 >= 1.50 -> Alerta CRITICAL)
        comp_safety_over = comp_repo.create(
            code="COMP-SEG-NR12",
            title="Operação Segura e Proteção de Placa NR-12",
            category=CompetencyCategory.SAFETY,
            description="Cumprir protocolos de segurança em máquina rotativa.",
        )
        # 3. Competência de Precisão Técnica para cenário UNDERCONFIDENCE_SUPPORT (4.50 - 2 = 2.50 >= 1.50)
        comp_under = comp_repo.create(
            code="COMP-PRE-01",
            title="Ajuste de Tolerância ISO H7 com Micrômetro",
            category=CompetencyCategory.TECHNICAL,
            description="Controlar tolerância H7 em eixo retificado.",
        )
        # 4. Competência sem entrega avaliada para cenário INSUFFICIENT_EVIDENCE
        comp_no_ev = comp_repo.create(
            code="COMP-INS-01",
            title="Recartilhamento Cruzado em Aço ABNT 1045",
            category=CompetencyCategory.TECHNICAL,
            description="Aplicar recartilha padronizada sem vibração.",
        )

        for comp in (comp_aligned, comp_safety_over, comp_under, comp_no_ev):
            session.add(
                ModuleCompetency(
                    module_id=module.id,
                    competency_id=comp.id,
                    weight=Decimal("1.50"),
                    required_level=4,
                )
            )

        enrollment = Enrollment(
            student_id=student.id,
            class_id=academic_class.id,
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(enrollment)
        session.add(
            TeacherAssignment(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            )
        )
        session.flush()

        # Cria uma PracticalTask e TaskSubmission avaliada para vincular as evidências práticas
        task = PracticalTask(
            module_id=module.id,
            class_id=academic_class.id,
            title="Peça Prática 01: Eixo Escalonado com Tolerância H7",
            description="Usinagem completa em torno horizontal.",
            due_date=now + timedelta(days=3),
            max_score=Decimal("10.00"),
            is_mandatory=True,
        )
        session.add(task)
        session.flush()

        criterion_no_ev = TaskCriterion(
            task_id=task.id,
            competency_id=comp_no_ev.id,
            criterion_name="Acabamento do Recartilhado Cruzado",
            weight=Decimal("1.00"),
            min_acceptable_level=3,
        )
        session.add(criterion_no_ev)

        submission = TaskSubmission(
            task_id=task.id,
            student_id=student.id,
            enrollment_id=enrollment.id,
            status=SubmissionStatus.EVALUATED,
            completed_at=now,
            final_task_score=Decimal("7.50"),
        )
        session.add(submission)
        session.flush()

        # Registra evidências práticas (DB-033) para 3 das 4 competências
        session.add_all(
            [
                SkillEvidence(
                    student_id=student.id,
                    competency_id=comp_aligned.id,
                    source_submission_id=submission.id,
                    verified_level=Decimal("3.50"),
                    verified_by=teacher.id,
                ),
                SkillEvidence(
                    student_id=student.id,
                    competency_id=comp_safety_over.id,
                    source_submission_id=submission.id,
                    verified_level=Decimal("2.00"),
                    verified_by=teacher.id,
                ),
                SkillEvidence(
                    student_id=student.id,
                    competency_id=comp_under.id,
                    source_submission_id=submission.id,
                    verified_level=Decimal("4.50"),
                    verified_by=teacher.id,
                ),
            ]
        )

        form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Questionário de Autoavaliação — Módulo 1",
            opens_at=now - timedelta(days=1),
            closes_at=now + timedelta(days=5),
            is_active=True,
            created_by=teacher.id,
        )
        session.add(form)
        session.commit()

        class_id = academic_class.id
        module_id = module.id
        form_id = form.id
        task_id = task.id
        criterion_no_ev_id = criterion_no_ev.id
        comp_aligned_id = comp_aligned.id
        comp_safety_over_id = comp_safety_over.id
        comp_under_id = comp_under.id
        comp_no_ev_id = comp_no_ev.id

    # 1. Estudante submete as 4 respostas de autoavaliação via POST /api/v1/self-assessments/submit
    submit_res = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "form_id": str(form_id),
            "responses": [
                {
                    "competency_id": str(comp_aligned_id),
                    "perceived_level": 4,
                    "confidence_score": 4,
                    "difficulty_notes": "Execução tranquila.",
                },
                {
                    "competency_id": str(comp_safety_over_id),
                    "perceived_level": 5,
                    "confidence_score": 5,
                    "difficulty_notes": "Acho que dominei todas as regras de segurança.",
                },
                {
                    "competency_id": str(comp_under_id),
                    "perceived_level": 2,
                    "confidence_score": 2,
                    "difficulty_notes": "Insegurança na leitura centesimal do micrômetro.",
                },
                {
                    "competency_id": str(comp_no_ev_id),
                    "perceived_level": 4,
                    "confidence_score": 3,
                    "difficulty_notes": None,
                },
            ],
        },
    )
    assert submit_res.status_code == status.HTTP_201_CREATED

    # 2. Professor executa explicitamente POST /api/v1/classes/{class_id}/diagnostics/evaluate
    eval_res = await client.post(
        f"/api/v1/classes/{class_id}/diagnostics/evaluate?module_id={module_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert eval_res.status_code == status.HTTP_200_OK
    eval_body = eval_res.json()

    assert eval_body["total_diagnostics_generated"] == 4
    assert eval_body["aligned_count"] == 1
    assert eval_body["overconfidence_risk_count"] == 1
    assert eval_body["underconfidence_support_count"] == 1
    assert eval_body["insufficient_evidence_count"] == 1
    assert eval_body["pedagogical_alerts_triggered_count"] == 1
    assert (
        eval_body["ethical_disclaimer"]
        == SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER
    )

    diags_by_comp = {d["competency_id"]: d for d in eval_body["diagnostics"]}

    # Verifica que todo diagnóstico possui explanation_text, evidências utilizadas e limitations_note
    for comp_key, diag_item in diags_by_comp.items():
        assert len(diag_item["explanation_text"]) >= 20
        assert len(diag_item["limitations_note"]) >= 20
        assert (
            SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER
            in diag_item["limitations_note"]
        )
        assert len(diag_item["recommended_action"]) >= 10
        if comp_key != str(comp_no_ev_id):
            assert diag_item["evidence_count"] == 1
            assert len(diag_item["evidences_used"]) == 1
            assert (
                diag_item["evidences_used"][0]["task_title"]
                == "Peça Prática 01: Eixo Escalonado com Tolerância H7"
            )
        else:
            assert diag_item["evidence_count"] == 0
            assert diag_item["evidences_used"] == []

    # Verifica alerta pedagógico gerado para divergência crítica na competência de segurança (COMP-SEG-NR12)
    safety_diag = diags_by_comp[str(comp_safety_over_id)]
    assert safety_diag["diagnostic_type"] == "OVERCONFIDENCE_RISK"
    assert safety_diag["pedagogical_alert_triggered"] is True
    assert safety_diag["pedagogical_alert_id"] is not None

    with db_session_factory() as session:
        alerts = list(
            session.scalars(
                select(AcademicAlert).where(
                    AcademicAlert.student_id == student.id,
                    AcademicAlert.alert_category == AlertCategory.SELF_EVAL_GAP,
                    AcademicAlert.status == AlertStatus.ACTIVE,
                )
            ).all()
        )
        assert len(alerts) == 1
        assert alerts[0].risk_level == RiskLevel.CRITICAL
        assert "COMP-SEG-NR12" in alerts[0].explainable_reason
        assert alerts[0].metric_snapshot is not None
        assert (
            alerts[0].metric_snapshot["competency_id"]
            == str(comp_safety_over_id)
        )
        assert len(alerts[0].metric_snapshot["evidences_used"]) == 1

    # 3. Professor não alocado na turma recebe 403 Forbidden
    forbidden_res = await client.post(
        f"/api/v1/classes/{class_id}/diagnostics/evaluate",
        headers={"Authorization": f"Bearer {other_teacher_token}"},
    )
    assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        forbidden_res.json()["message"] == DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE
    )

    # 4. Quando o docente avalia uma entrega prática (BE-025) para a competência que estava sem evidência (comp_no_ev)
    # com nota baixa (achieved_level = 1 vs perceived_level = 4 -> gap +3.00 em TECHNICAL), o diagnóstico é atualizado
    # de INSUFFICIENT_EVIDENCE para OVERCONFIDENCE_RISK e gera novo alerta pedagógico de precisão técnica!
    be025_res = await client.post(
        f"/api/v1/tasks/{task_id}/evaluations",
        headers={"Authorization": f"Bearer {teacher_token}"},
        json={
            "student_id": str(student.id),
            "status": "EVALUATED",
            "evaluations": [
                {
                    "criterion_id": str(criterion_no_ev_id),
                    "achieved_level": 1,
                    "technical_feedback": "Passo da recartilha desalinhado e fora da especificação técnica.",
                }
            ],
        },
    )
    assert be025_res.status_code == status.HTTP_200_OK

    with db_session_factory() as session:
        updated_diag = session.scalar(
            select(ExplainableDiagnostic).where(
                ExplainableDiagnostic.student_id == student.id,
                ExplainableDiagnostic.competency_id == comp_no_ev_id,
            )
        )
        assert updated_diag is not None
        assert updated_diag.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK
        assert updated_diag.discrepancy_gap == Decimal("3.00")

        active_gap_alerts = list(
            session.scalars(
                select(AcademicAlert).where(
                    AcademicAlert.student_id == student.id,
                    AcademicAlert.alert_category == AlertCategory.SELF_EVAL_GAP,
                    AcademicAlert.status == AlertStatus.ACTIVE,
                )
            ).all()
        )
        # Agora existem 2 alertas ativos de SELF_EVAL_GAP (COMP-SEG-NR12 e COMP-INS-01)
        assert len(active_gap_alerts) == 2
