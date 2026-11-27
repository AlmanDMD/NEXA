"""Testes unitários, de integração, segurança (IDOR/RBAC) e cruzamento diagnóstico para Submissão de Autoavaliação pelo Aluno (BE-036)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

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
from app.core.class_period_guard import CLASS_PERIOD_CLOSED_ERROR_CODE
from app.main import create_app
from app.models import (
    Base,
    Competency,
    Enrollment,
    ExplainableDiagnostic,
    ModuleCompetency,
    SelfAssessmentForm,
    SkillEvidence,
    StudentSelfAssessment,
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
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.self_assessment_service import (
    SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_DEADLINE_EXPIRED_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_INACTIVE_FORM_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_INVALID_COMPETENCY_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_NOT_OPEN_YET_MESSAGE,
    SELF_ASSESSMENT_SUBMIT_ROLE_FORBIDDEN_MESSAGE,
    compute_competency_explainable_diagnostic,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "self_assessment_submit_test.db"
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
def submit_app(
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
async def client(submit_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=submit_app)
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


def _seed_submission_environment(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> dict[str, Any]:
    """Cria curso, turma ativa, módulo com 3 competências, evidências práticas do docente e formulário aberto."""
    teacher, teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.tornearia@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Carlos Tornearia",
        registration_number="PROF-2026-0361",
    )
    student_1, student_1_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno1.submissao@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Um Submissão",
        registration_number="ALU-2026-0361",
    )
    student_2, student_2_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno2.colega@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Dois Colega",
        registration_number="ALU-2026-0362",
    )
    outsider_student, outsider_student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.nao.matriculado@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Sem Matrícula",
        registration_number="ALU-2026-0363",
    )

    now = datetime.now(timezone.utc)

    with db_session_factory() as session:
        course = CourseRepository(session=session).create(
            name="Técnico em Usinagem Mecânica",
            code="TEC-USI-036",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session=session).create(
            course_id=course.id,
            code="USI-2026-S4",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=35,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 15),
        )
        subject = SubjectRepository(session=session).create(
            course_id=course.id,
            name="Processos de Tornearia Convencional",
            code="TOR-CONV-036",
            workload_hours=100,
            is_active=True,
        )
        module = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 1: Torneamento Cilíndrico e Faceamento",
            order_index=1,
            description="Operação de torno mecânico horizontal e controle dimensional.",
            practical_hours=50,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )

        comp_repo = CompetencyRepository(session=session)
        comp_1 = comp_repo.create(
            code="COMP-TOR-01",
            title="Centragem e Fixação em Placa Universal",
            category=CompetencyCategory.TECHNICAL,
            description="Fixar e centrar tarugo cilíndrico com batimento radial controlado.",
        )
        comp_2 = comp_repo.create(
            code="COMP-TOR-02",
            title="Afiação ePosicionamento de Ferramenta de Corte",
            category=CompetencyCategory.PROCEDURAL,
            description="Posicionar ferramenta na altura do ponto rotativo e ajustar ângulos.",
        )
        comp_3 = comp_repo.create(
            code="COMP-SEG-02",
            title="Segurança em Máquina Rotativa NR-12",
            category=CompetencyCategory.SAFETY,
            description="Operar com proteção de placa, óculos de segurança e parada de emergência.",
        )
        unlinked_comp = comp_repo.create(
            code="COMP-EXT-99",
            title="Soldagem TIG em Aço Inoxidável",
            category=CompetencyCategory.TECHNICAL,
            description="Competência que pertence a outro módulo.",
        )

        session.add_all(
            [
                ModuleCompetency(
                    module_id=module.id,
                    competency_id=comp_1.id,
                    weight=Decimal("2.00"),
                    required_level=4,
                ),
                ModuleCompetency(
                    module_id=module.id,
                    competency_id=comp_2.id,
                    weight=Decimal("1.50"),
                    required_level=3,
                ),
                ModuleCompetency(
                    module_id=module.id,
                    competency_id=comp_3.id,
                    weight=Decimal("1.50"),
                    required_level=4,
                ),
                TeacherAssignment(
                    teacher_id=teacher.id,
                    class_id=academic_class.id,
                    subject_id=subject.id,
                ),
                Enrollment(
                    student_id=student_1.id,
                    class_id=academic_class.id,
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=student_2.id,
                    class_id=academic_class.id,
                    status=EnrollmentStatus.ACTIVE,
                ),
                # Evidências práticas previamente registradas pelo docente para o Aluno 1 (DB-033):
                # COMP-TOR-01: verified_level = 2.00 (se aluno declarar 5 -> gap +3.00 -> OVERCONFIDENCE_RISK)
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp_1.id,
                    verified_level=Decimal("2.00"),
                    verified_by=teacher.id,
                ),
                # COMP-TOR-02: verified_level = 4.50 (se aluno declarar 2 -> gap -2.50 -> UNDERCONFIDENCE_SUPPORT)
                SkillEvidence(
                    student_id=student_1.id,
                    competency_id=comp_2.id,
                    verified_level=Decimal("4.50"),
                    verified_by=teacher.id,
                ),
                # COMP-SEG-02: sem evidência registrada -> INSUFFICIENT_EVIDENCE
            ]
        )

        active_form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Autoavaliação — Tornearia Módulo 1",
            instructions="Avalie de 1 a 5 seu domínio prático e confiança.",
            opens_at=now - timedelta(days=1),
            closes_at=now + timedelta(days=5),
            is_active=True,
            created_by=teacher.id,
        )
        expired_form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Autoavaliação Encerrada",
            opens_at=now - timedelta(days=10),
            closes_at=now - timedelta(days=2),
            is_active=True,
            created_by=teacher.id,
        )
        future_form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Autoavaliação Futura",
            opens_at=now + timedelta(days=2),
            closes_at=now + timedelta(days=8),
            is_active=True,
            created_by=teacher.id,
        )
        inactive_form = SelfAssessmentForm(
            module_id=module.id,
            class_id=academic_class.id,
            title="Autoavaliação Inativa",
            opens_at=now - timedelta(days=1),
            closes_at=now + timedelta(days=5),
            is_active=False,
            created_by=teacher.id,
        )
        session.add_all([active_form, expired_form, future_form, inactive_form])
        session.commit()

        return {
            "class": academic_class,
            "subject": subject,
            "module": module,
            "comp_1": comp_1,
            "comp_2": comp_2,
            "comp_3": comp_3,
            "unlinked_comp": unlinked_comp,
            "active_form": active_form,
            "expired_form": expired_form,
            "future_form": future_form,
            "inactive_form": inactive_form,
            "teacher": teacher,
            "teacher_token": teacher_token,
            "student_1": student_1,
            "student_1_token": student_1_token,
            "student_2": student_2,
            "student_2_token": student_2_token,
            "outsider_student": outsider_student,
            "outsider_student_token": outsider_student_token,
        }


def test_compute_competency_explainable_diagnostic_unit() -> None:
    """Testa unitariamente o algoritmo de cruzamento diagnóstico (OVERCONFIDENCE, UNDERCONFIDENCE, ALIGNED, INSUFFICIENT_EVIDENCE)."""
    comp = Competency(
        code="COMP-TOR-01",
        title="Centragem em Placa Universal",
        category=CompetencyCategory.TECHNICAL,
    )

    # 1. OVERCONFIDENCE_RISK (gap >= +1.50)
    self_lvl, teacher_lvl, gap, diag_type, expl, lim, act = (
        compute_competency_explainable_diagnostic(
            competency=comp,
            module_title="Tornearia 1",
            perceived_level=5,
            confidence_score=5,
            difficulty_notes=None,
            avg_verified_level=Decimal("3.00"),
            evidence_count=2,
        )
    )
    assert self_lvl == Decimal("5.00")
    assert teacher_lvl == Decimal("3.00")
    assert gap == Decimal("2.00")
    assert diag_type == DiagnosticType.OVERCONFIDENCE_RISK
    assert len(expl) >= 10 and len(lim) >= 10 and len(act) >= 5

    # 2. UNDERCONFIDENCE_SUPPORT (gap <= -1.50)
    self_lvl, teacher_lvl, gap, diag_type, _, _, _ = (
        compute_competency_explainable_diagnostic(
            competency=comp,
            module_title="Tornearia 1",
            perceived_level=2,
            confidence_score=2,
            difficulty_notes="Insegurança no ajuste fino.",
            avg_verified_level=Decimal("4.00"),
            evidence_count=3,
        )
    )
    assert gap == Decimal("-2.00")
    assert diag_type == DiagnosticType.UNDERCONFIDENCE_SUPPORT

    # 3. ALIGNED (|gap| < 1.50)
    _, _, gap, diag_type, _, _, _ = compute_competency_explainable_diagnostic(
        competency=comp,
        module_title="Tornearia 1",
        perceived_level=4,
        confidence_score=4,
        difficulty_notes=None,
        avg_verified_level=Decimal("3.50"),
        evidence_count=1,
    )
    assert gap == Decimal("0.50")
    assert diag_type == DiagnosticType.ALIGNED

    # 4. INSUFFICIENT_EVIDENCE (evidence_count == 0)
    _, _, gap, diag_type, _, _, _ = compute_competency_explainable_diagnostic(
        competency=comp,
        module_title="Tornearia 1",
        perceived_level=3,
        confidence_score=3,
        difficulty_notes=None,
        avg_verified_level=None,
        evidence_count=0,
    )
    assert gap == Decimal("0.00")
    assert diag_type == DiagnosticType.INSUFFICIENT_EVIDENCE


@pytest.mark.asyncio
async def test_submit_self_assessment_persists_responses_triggers_diagnostics_and_suggests_help_request(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 1 + Descrição + Regra de Negócio: POST /api/v1/self-assessments/submit (201) grava respostas, sugere pedido de ajuda quando perceived_level <= 2 e dispara cruzamento diagnóstico."""
    env = _seed_submission_environment(db_session_factory, fast_hasher)

    response = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": [
                {
                    "competency_id": str(env["comp_1"].id),
                    "perceived_level": 5,
                    "confidence_score": 5,
                    "difficulty_notes": "Consigo centrar rapidamente na placa.",
                },
                {
                    "competency_id": str(env["comp_2"].id),
                    "perceived_level": 2,
                    "confidence_score": 2,
                    "difficulty_notes": "Tive dificuldade na altura do gume cortante da ferramenta.",
                },
                {
                    "competency_id": str(env["comp_3"].id),
                    "perceived_level": 4,
                    "confidence_score": 4,
                    "difficulty_notes": None,
                },
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["form_id"] == str(env["active_form"].id)
    assert body["student_id"] == str(env["student_1"].id)
    assert body["total_submitted"] == 3
    assert body["created_count"] == 3
    assert body["updated_count"] == 0
    assert body["is_form_completed"] is True
    assert body["diagnostic_triggered"] is True

    # Verifica sugestão de pedido de ajuda (COMP-TOR-02 teve perceived_level = 2 <= 2)
    assert body["suggest_help_request"] is True
    help_sugg = body["help_request_suggestion"]
    assert help_sugg["should_suggest_help_request"] is True
    assert help_sugg["high_difficulty_count"] == 1
    assert help_sugg["suggested_category"] == "PRACTICAL_DIFFICULTY"
    assert help_sugg["module_id"] == str(env["module"].id)
    assert help_sugg["subject_id"] == str(env["subject"].id)
    assert len(help_sugg["flagged_competencies"]) == 1
    assert help_sugg["flagged_competencies"][0]["competency_id"] == str(
        env["comp_2"].id
    )
    assert help_sugg["flagged_competencies"][0]["perceived_level"] == 2

    # Verifica diagnósticos explicáveis gerados e persistidos no banco
    diags_by_comp = {d["competency_id"]: d for d in body["diagnostics"]}
    assert len(diags_by_comp) == 3

    # COMP-TOR-01: perceived 5.00 vs teacher 2.00 -> gap +3.00 -> OVERCONFIDENCE_RISK
    d1 = diags_by_comp[str(env["comp_1"].id)]
    assert d1["diagnostic_type"] == "OVERCONFIDENCE_RISK"
    assert d1["discrepancy_gap"] == "3.00"
    assert d1["evidence_count"] == 1

    # COMP-TOR-02: perceived 2.00 vs teacher 4.50 -> gap -2.50 -> UNDERCONFIDENCE_SUPPORT
    d2 = diags_by_comp[str(env["comp_2"].id)]
    assert d2["diagnostic_type"] == "UNDERCONFIDENCE_SUPPORT"
    assert d2["discrepancy_gap"] == "-2.50"
    assert d2["evidence_count"] == 1

    # COMP-SEG-02: sem evidência docente -> INSUFFICIENT_EVIDENCE
    d3 = diags_by_comp[str(env["comp_3"].id)]
    assert d3["diagnostic_type"] == "INSUFFICIENT_EVIDENCE"
    assert d3["evidence_count"] == 0

    # Confirma persistência real nas tabelas student_self_assessments e explainable_diagnostics
    with db_session_factory() as session:
        saved_answers = list(
            session.scalars(
                select(StudentSelfAssessment).where(
                    StudentSelfAssessment.form_id == env["active_form"].id,
                    StudentSelfAssessment.student_id == env["student_1"].id,
                )
            ).all()
        )
        assert len(saved_answers) == 3

        saved_diags = list(
            session.scalars(
                select(ExplainableDiagnostic).where(
                    ExplainableDiagnostic.student_id == env["student_1"].id,
                    ExplainableDiagnostic.module_id == env["module"].id,
                )
            ).all()
        )
        assert len(saved_diags) == 3

    # Reenvio pelo mesmo estudante dentro do prazo atualiza registros existentes (upsert sem violar UNIQUE)
    # e quando todos perceived_level >= 3 não sugere pedido de ajuda
    res_update = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": [
                {
                    "competency_id": str(env["comp_2"].id),
                    "perceived_level": 4,
                    "confidence_score": 4,
                    "difficulty_notes": "Após praticar, ajustei a altura da ferramenta com segurança.",
                }
            ],
        },
    )
    assert res_update.status_code == status.HTTP_201_CREATED
    update_body = res_update.json()
    assert update_body["created_count"] == 0
    assert update_body["updated_count"] == 1
    assert update_body["suggest_help_request"] is False
    assert (
        update_body["help_request_suggestion"]["should_suggest_help_request"]
        is False
    )


@pytest.mark.asyncio
async def test_submit_self_assessment_validates_active_form_and_deadline_window(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 2: Valida se o formulário está ativo e dentro do prazo (opens_at <= now <= closes_at)."""
    env = _seed_submission_environment(db_session_factory, fast_hasher)
    sample_responses = [
        {
            "competency_id": str(env["comp_1"].id),
            "perceived_level": 3,
            "confidence_score": 3,
        }
    ]

    # 1. Formulário inativo -> 422
    res_inactive = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["inactive_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_inactive.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        res_inactive.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_INACTIVE_FORM_MESSAGE
    )

    # 2. Formulário com prazo encerrado -> 422
    res_expired = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["expired_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_expired.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        res_expired.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_DEADLINE_EXPIRED_MESSAGE
    )

    # 3. Formulário futuro (ainda não aberto) -> 422
    res_future = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["future_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_future.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        res_future.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_NOT_OPEN_YET_MESSAGE
    )

    # 4. Competência que não pertence ao módulo do formulário -> 400
    res_invalid_comp = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": [
                {
                    "competency_id": str(env["unlinked_comp"].id),
                    "perceived_level": 3,
                    "confidence_score": 3,
                }
            ],
        },
    )
    assert res_invalid_comp.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        res_invalid_comp.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_INVALID_COMPETENCY_MESSAGE
    )

    # 5. Escala fora do intervalo 1..5 -> 400
    res_out_of_scale = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": [
                {
                    "competency_id": str(env["comp_1"].id),
                    "perceived_level": 6,
                    "confidence_score": 0,
                }
            ],
        },
    )
    assert res_out_of_scale.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_submit_self_assessment_prevents_impersonation_and_enforces_rbac(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 3: Impede submissão em nome de outro aluno (usa current_user.id), bloqueia não-matriculados e docentes."""
    env = _seed_submission_environment(db_session_factory, fast_hasher)
    sample_responses = [
        {
            "competency_id": str(env["comp_1"].id),
            "perceived_level": 4,
            "confidence_score": 4,
        }
    ]

    # 1. Tentativa de submissão em nome de outro aluno (student_1 tentando enviar student_id do student_2) -> 403
    res_idor = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "student_id": str(env["student_2"].id),
            "responses": sample_responses,
        },
    )
    assert res_idor.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_idor.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_IDOR_FORBIDDEN_MESSAGE
    )

    # 2. Professor tentando submeter autoavaliação -> 403
    res_teacher = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_teacher.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_teacher.json()["message"]
        == SELF_ASSESSMENT_SUBMIT_ROLE_FORBIDDEN_MESSAGE
    )

    # 3. Estudante sem matrícula na turma do formulário -> 403
    res_outsider = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['outsider_student_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_outsider.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_outsider.json()["message"]
        == SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE
    )

    # 4. Turma com período letivo encerrado (COMPLETED) bloqueia submissão via check_class_is_active (BE-029)
    with db_session_factory() as session:
        cls = AcademicClassRepository(session=session).get_by_id(env["class"].id)
        assert cls is not None
        cls.status = ClassStatus.COMPLETED
        session.add(cls)
        session.commit()

    res_closed_class = await client.post(
        "/api/v1/self-assessments/submit",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json={
            "form_id": str(env["active_form"].id),
            "responses": sample_responses,
        },
    )
    assert res_closed_class.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert res_closed_class.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
