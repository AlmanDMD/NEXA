"""Testes unitários e de integração para o Endpoint de Consulta de Discrepâncias de Aprendizagem (EPIC-07 / BE-038)."""

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
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    Base,
    Enrollment,
    ModuleCompetency,
    PracticalTask,
    SelfAssessmentForm,
    SkillEvidence,
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
    ClassStatus,
    CompetencyCategory,
    DiagnosticType,
    EnrollmentStatus,
    Shift,
    SubmissionStatus,
    UserRole,
)
from app.schemas.self_assessment import (
    DiagnosticDiscrepanciesQueryParams,
    DiagnosticDiscrepanciesSummarySchema,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.diagnostic_service import (
    DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE,
    DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE,
    SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "diagnostic_discrepancies_test.db"
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
def test_app(
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
async def client(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=test_app)
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


def test_diagnostic_discrepancies_query_params_validation_unit() -> None:
    """Testa validação unitária do schema de query parameters e summary (BE-038)."""
    valid_params = DiagnosticDiscrepanciesQueryParams(
        page=2,
        page_size=25,
        diagnostic_type=DiagnosticType.OVERCONFIDENCE_RISK,
    )
    assert valid_params.page == 2
    assert valid_params.page_size == 25
    assert valid_params.diagnostic_type == DiagnosticType.OVERCONFIDENCE_RISK

    with pytest.raises(Exception):
        DiagnosticDiscrepanciesQueryParams(page=0)

    with pytest.raises(Exception):
        DiagnosticDiscrepanciesQueryParams(page_size=300)

    summary = DiagnosticDiscrepanciesSummarySchema(
        total_discrepancies=10,
        aligned_count=4,
        overconfidence_risk_count=3,
        underconfidence_support_count=2,
        insufficient_evidence_count=1,
        critical_alerts_count=2,
    )
    assert summary.total_discrepancies == 10
    assert summary.aligned_count == 4


@pytest.mark.asyncio
async def test_get_diagnostic_discrepancies_complete_flow(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios de Aceitação 1, 2 e 3 do BE-038:

    1. Rota GET /api/v1/diagnostics/discrepancies.
    2. Estudante visualiza apenas o próprio comparativo com linguagem pedagógica construtiva.
    3. Professor visualiza o mapa de divergências de toda a turma com filtros.
    4. Valida bloqueio contextual (403) para docente não alocado e para estudante tentando ver outro aluno.
    """
    teacher, teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.usinagem@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Mecânica SENAI",
        registration_number="PROF-2026-0381",
    )
    other_teacher, other_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.sem.atribuicao@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Sem Turma",
        registration_number="PROF-2026-0382",
    )
    coordinator, coordinator_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord.pedagogico@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coord. Pedagógico SENAI",
        registration_number="COORD-2026-0381",
    )
    student_1, student_1_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno1.discrepancy@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Um Discrepância",
        registration_number="ALU-2026-0381",
    )
    student_2, student_2_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno2.discrepancy@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Dois Discrepância",
        registration_number="ALU-2026-0382",
    )

    now = datetime.now(timezone.utc)

    with db_session_factory() as session:
        course = CourseRepository(session=session).create(
            name="Técnico em Usinagem e Automação",
            code="TEC-USI-038",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session=session).create(
            course_id=course.id,
            code="USI-2026-038",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 15),
        )
        subject = SubjectRepository(session=session).create(
            course_id=course.id,
            name="Tornearia Mecânica e Tolerâncias",
            code="TOR-TOL-038",
            workload_hours=100,
            is_active=True,
        )
        module = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 1: Operações Básicas de Torneamento",
            order_index=1,
            description="Operações de usinagem e medições centesimais.",
            practical_hours=60,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )

        comp_repo = CompetencyRepository(session=session)
        # 1. ALIGNED: percepção 4 vs verificado 3.50 -> gap +0.50
        comp_aligned = comp_repo.create(
            code="COMP-ALI-01",
            title="Faceamento Perpendicular e Desbaste",
            category=CompetencyCategory.PROCEDURAL,
            description="Executar faceamento mantendo planaridade.",
        )
        # 2. OVERCONFIDENCE_RISK: percepção 5 vs verificado 2.00 -> gap +3.00 em SAFETY -> Alerta Crítico
        comp_safety = comp_repo.create(
            code="COMP-SEG-01",
            title="Proteção de Placa e Segurança NR-12",
            category=CompetencyCategory.SAFETY,
            description="Normas de segurança operacional em oficina.",
        )
        # 3. UNDERCONFIDENCE_SUPPORT: percepção 2 vs verificado 4.50 -> gap -2.50
        comp_under = comp_repo.create(
            code="COMP-UND-01",
            title="Ajuste de Tolerância ISO H7",
            category=CompetencyCategory.TECHNICAL,
            description="Usinagem de eixo com tolerância centesimal.",
        )
        # 4. INSUFFICIENT_EVIDENCE: percepção 4 sem entregas avaliadas
        comp_no_ev = comp_repo.create(
            code="COMP-INS-01",
            title="Recartilhado Cruzado em Aço 1045",
            category=CompetencyCategory.TECHNICAL,
            description="Acabamento superficial com recartilha.",
        )

        for comp in (comp_aligned, comp_safety, comp_under, comp_no_ev):
            session.add(
                ModuleCompetency(
                    module_id=module.id,
                    competency_id=comp.id,
                    weight=Decimal("1.50"),
                    required_level=4,
                )
            )

        enr_1 = Enrollment(
            student_id=student_1.id,
            class_id=academic_class.id,
            status=EnrollmentStatus.ACTIVE,
        )
        enr_2 = Enrollment(
            student_id=student_2.id,
            class_id=academic_class.id,
            status=EnrollmentStatus.ACTIVE,
        )
        session.add_all([enr_1, enr_2])

        session.add(
            TeacherAssignment(
                teacher_id=teacher.id,
                class_id=academic_class.id,
                subject_id=subject.id,
            )
        )
        session.flush()

        task = PracticalTask(
            module_id=module.id,
            class_id=academic_class.id,
            title="Usinagem de Eixo Padrão SENAI",
            description="Atividade prática com tolerâncias H7.",
            due_date=now + timedelta(days=3),
            max_score=Decimal("10.00"),
            is_mandatory=True,
        )
        session.add(task)
        session.flush()

        sub_1 = TaskSubmission(
            task_id=task.id,
            student_id=student_1.id,
            enrollment_id=enr_1.id,
            status=SubmissionStatus.EVALUATED,
            completed_at=now,
            final_task_score=Decimal("8.00"),
        )
        session.add(sub_1)
        session.flush()

        session.add_all(
            [
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp_aligned.id,
                    source_submission_id=sub_1.id,
                    verified_level=Decimal("3.50"),
                    verified_by=teacher.id,
                ),
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp_safety.id,
                    source_submission_id=sub_1.id,
                    verified_level=Decimal("2.00"),
                    verified_by=teacher.id,
                ),
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp_under.id,
                    source_submission_id=sub_1.id,
                    verified_level=Decimal("4.50"),
                    verified_by=teacher.id,
                ),
            ]
        )

        form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Autoavaliação Prática — Módulo 1",
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
        comp_aligned_id = comp_aligned.id
        comp_safety_id = comp_safety.id
        comp_under_id = comp_under.id
        comp_no_ev_id = comp_no_ev.id

    # Aluno 1 submete suas respostas de autoavaliação
    submit_res = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {student_1_token}"},
        json={
            "form_id": str(form_id),
            "responses": [
                {
                    "competency_id": str(comp_aligned_id),
                    "perceived_level": 4,
                    "confidence_score": 4,
                },
                {
                    "competency_id": str(comp_safety_id),
                    "perceived_level": 5,
                    "confidence_score": 5,
                },
                {
                    "competency_id": str(comp_under_id),
                    "perceived_level": 2,
                    "confidence_score": 2,
                    "difficulty_notes": "Insegurança ao manusear micrômetro no acabamento.",
                },
                {
                    "competency_id": str(comp_no_ev_id),
                    "perceived_level": 4,
                    "confidence_score": 3,
                },
            ],
        },
    )
    assert submit_res.status_code == status.HTTP_201_CREATED

    # -------------------------------------------------------------------------
    # CRITÉRIO 2: Estudante visualiza apenas o próprio comparativo com linguagem construtiva
    # -------------------------------------------------------------------------
    stu_res = await client.get(
        "/api/v1/diagnostics/discrepancies",
        headers={"Authorization": f"Bearer {student_1_token}"},
    )
    assert stu_res.status_code == status.HTTP_200_OK
    stu_body = stu_res.json()

    assert stu_body["total"] == 4
    assert stu_body["summary"]["total_discrepancies"] == 4
    assert stu_body["summary"]["aligned_count"] == 1
    assert stu_body["summary"]["overconfidence_risk_count"] == 1
    assert stu_body["summary"]["underconfidence_support_count"] == 1
    assert stu_body["summary"]["insufficient_evidence_count"] == 1
    assert stu_body["summary"]["critical_alerts_count"] == 1
    assert stu_body["ethical_disclaimer"] == SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER

    # Todos os itens pertencem ao Aluno 1
    for item in stu_body["discrepancies"]:
        assert item["student_id"] == str(student_1.id)
        assert item["student_name"] == "Aluno Um Discrepância"
        assert item["class_id"] == str(class_id)
        assert item["module_id"] == str(module_id)
        assert len(item["explanation_text"]) >= 20
        assert len(item["limitations_note"]) >= 20
        assert len(item["recommended_action"]) >= 10
        # Linguagem pedagógica construtiva e disclaimer explícito
        assert SELF_ASSESSMENT_NON_DEFINITIVE_DISCLAIMER in item["limitations_note"]

    # Verifica lista de evidências práticas para as competências avaliadas
    comp_map = {item["competency_id"]: item for item in stu_body["discrepancies"]}
    assert comp_map[str(comp_aligned_id)]["evidence_count"] == 1
    assert (
        comp_map[str(comp_aligned_id)]["evidences_used"][0]["task_title"]
        == "Usinagem de Eixo Padrão SENAI"
    )
    assert comp_map[str(comp_no_ev_id)]["evidence_count"] == 0
    assert comp_map[str(comp_no_ev_id)]["evidences_used"] == []

    # CRITÉRIO 2 (Segurança): Estudante tenta consultar o student_id de outro aluno e recebe 403 Forbidden
    stu_forbidden_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?student_id={student_2.id}",
        headers={"Authorization": f"Bearer {student_1_token}"},
    )
    assert stu_forbidden_res.status_code == status.HTTP_403_FORBIDDEN
    assert stu_forbidden_res.json()["message"] == DIAGNOSTIC_STUDENT_FORBIDDEN_MESSAGE

    # -------------------------------------------------------------------------
    # CRITÉRIO 3: Professor visualiza o mapa de divergências de toda a turma com filtros
    # -------------------------------------------------------------------------
    prof_all_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert prof_all_res.status_code == status.HTTP_200_OK
    prof_all_body = prof_all_res.json()
    assert prof_all_body["total"] == 4
    assert prof_all_body["filters"]["class_id"] == str(class_id)

    # Filtro por tipo de divergência: OVERCONFIDENCE_RISK
    prof_overconf_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}&diagnostic_type=OVERCONFIDENCE_RISK",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert prof_overconf_res.status_code == status.HTTP_200_OK
    overconf_body = prof_overconf_res.json()
    assert overconf_body["total"] == 1
    assert (
        overconf_body["discrepancies"][0]["competency_id"]
        == str(comp_safety_id)
    )
    assert (
        overconf_body["discrepancies"][0]["diagnostic_type"]
        == "OVERCONFIDENCE_RISK"
    )
    assert overconf_body["discrepancies"][0]["pedagogical_alert_triggered"] is True
    assert overconf_body["discrepancies"][0]["pedagogical_alert_id"] is not None

    # Filtro por módulo e competência específica
    prof_comp_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}&module_id={module_id}&competency_id={comp_under_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert prof_comp_res.status_code == status.HTTP_200_OK
    comp_body = prof_comp_res.json()
    assert comp_body["total"] == 1
    assert comp_body["discrepancies"][0]["competency_id"] == str(comp_under_id)
    assert (
        comp_body["discrepancies"][0]["diagnostic_type"]
        == "UNDERCONFIDENCE_SUPPORT"
    )

    # -------------------------------------------------------------------------
    # SEGURANÇA DOCENTE: Professor sem atribuição na turma recebe 403 Forbidden
    # -------------------------------------------------------------------------
    other_prof_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}",
        headers={"Authorization": f"Bearer {other_teacher_token}"},
    )
    assert other_prof_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        other_prof_res.json()["message"]
        == DIAGNOSTIC_TEACHER_FORBIDDEN_MESSAGE
    )

    # -------------------------------------------------------------------------
    # COORDENAÇÃO PEDAGÓGICA: Acesso irrestrito com visão agregada
    # -------------------------------------------------------------------------
    coord_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}",
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert coord_res.status_code == status.HTTP_200_OK
    assert coord_res.json()["total"] == 4

    # -------------------------------------------------------------------------
    # PAGINAÇÃO: Testa page=1 e page_size=2
    # -------------------------------------------------------------------------
    page_res = await client.get(
        f"/api/v1/diagnostics/discrepancies?class_id={class_id}&page=1&page_size=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert page_res.status_code == status.HTTP_200_OK
    page_body = page_res.json()
    assert page_body["total"] == 4
    assert page_body["page"] == 1
    assert page_body["page_size"] == 2
    assert page_body["total_pages"] == 2
    assert len(page_body["discrepancies"]) == 2
    # O sumário analítico preserva o cômputo global do filtro
    assert page_body["summary"]["total_discrepancies"] == 4
