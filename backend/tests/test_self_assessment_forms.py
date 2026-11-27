"""Testes unitários, de integração e RBAC para Questionários de Autoavaliação de Competências (BE-035)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

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
from app.core.class_period_guard import CLASS_PERIOD_CLOSED_ERROR_CODE
from app.main import create_app
from app.models import (
    Base,
    Enrollment,
    ModuleCompetency,
    SelfAssessmentForm,
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
    EnrollmentStatus,
    Shift,
    UserRole,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.self_assessment_service import (
    SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE,
    SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE,
    SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE,
    is_form_window_open,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "self_assessment_forms_test.db"
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
def self_assessment_app(
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
async def client(self_assessment_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=self_assessment_app)
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
    full_name: str = "Usuário SENAI",
    registration_number: str = "SENAI-2026-0001",
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


def _seed_academic_environment(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> dict[str, Any]:
    """Cria curso, turma ativa, disciplinas, módulos (com e sem competências), docentes e estudantes."""
    teacher, teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.metrologia@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Ricardo Tornearia",
        registration_number="PROF-2026-0351",
    )
    other_teacher, other_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.outro@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Outro Docente",
        registration_number="PROF-2026-0352",
    )
    coordinator, coordinator_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord.mecanica@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coordenador Mecânica",
        registration_number="COORD-2026-0351",
    )
    student_1, student_1_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno1.auto@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Um Autoavaliação",
        registration_number="ALU-2026-0351",
    )
    student_2, student_2_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno2.auto@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Dois Autoavaliação",
        registration_number="ALU-2026-0352",
    )
    outsider_student, outsider_student_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.externo@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Fora da Turma",
        registration_number="ALU-2026-0353",
    )

    with db_session_factory() as session:
        course = CourseRepository(session=session).create(
            name="Técnico em Mecânica de Precisão",
            code="TEC-MEC-035",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        academic_class = AcademicClassRepository(session=session).create(
            course_id=course.id,
            code="MEC-2026-S4",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=35,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 15),
        )
        subject = SubjectRepository(session=session).create(
            course_id=course.id,
            name="Metrologia e Controle Dimensional",
            code="MET-DIM-035",
            workload_hours=80,
            is_active=True,
        )
        module_with_comps = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 1: Instrumentos de Medição Direta",
            order_index=1,
            description="Uso de paquímetro universal, micrômetro externo e relógio comparador.",
            practical_hours=40,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )
        module_2_with_comps = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 2: Tolerâncias ISO e Ajustes",
            order_index=2,
            description="Controle de eixos e furos H7/g6.",
            practical_hours=40,
            module_weight=Decimal("1.50"),
            passing_score=Decimal("6.00"),
        )
        module_without_comps = LearningModuleRepository(session=session).create(
            subject_id=subject.id,
            title="Módulo 3: Módulo Sem Competências",
            order_index=3,
            description="Módulo ainda sem competências vinculadas.",
            practical_hours=20,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )

        comp_repo = CompetencyRepository(session=session)
        comp_1 = comp_repo.create(
            code="COMP-MET-01",
            title="Leitura com Paquímetro Universal 0,02mm",
            category=CompetencyCategory.TECHNICAL,
            description="Realizar medições externas, internas e de profundidade com resolução de 0,02mm.",
        )
        comp_2 = comp_repo.create(
            code="COMP-MET-02",
            title="Medição com Micrômetro Externo Centesimal",
            category=CompetencyCategory.TECHNICAL,
            description="Aferir diâmetros de precisão utilizando catraca e compensação térmica.",
        )
        comp_3 = comp_repo.create(
            code="COMP-SEG-01",
            title="Conservação e Limpeza de Instrumentos",
            category=CompetencyCategory.SAFETY,
            description="Zelar pela integridade metrológica e armazenamento adequado na bancada.",
        )

        session.add_all(
            [
                ModuleCompetency(
                    module_id=module_with_comps.id,
                    competency_id=comp_1.id,
                    weight=Decimal("2.00"),
                    required_level=4,
                ),
                ModuleCompetency(
                    module_id=module_with_comps.id,
                    competency_id=comp_2.id,
                    weight=Decimal("1.50"),
                    required_level=3,
                ),
                ModuleCompetency(
                    module_id=module_with_comps.id,
                    competency_id=comp_3.id,
                    weight=Decimal("1.00"),
                    required_level=4,
                ),
                ModuleCompetency(
                    module_id=module_2_with_comps.id,
                    competency_id=comp_2.id,
                    weight=Decimal("2.00"),
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
            ]
        )
        session.commit()

        return {
            "course": course,
            "class": academic_class,
            "subject": subject,
            "module_with_comps": module_with_comps,
            "module_2_with_comps": module_2_with_comps,
            "module_without_comps": module_without_comps,
            "competencies": [comp_1, comp_2, comp_3],
            "teacher": teacher,
            "teacher_token": teacher_token,
            "other_teacher": other_teacher,
            "other_teacher_token": other_teacher_token,
            "coordinator": coordinator,
            "coordinator_token": coordinator_token,
            "student_1": student_1,
            "student_1_token": student_1_token,
            "student_2": student_2,
            "student_2_token": student_2_token,
            "outsider_student": outsider_student,
            "outsider_student_token": outsider_student_token,
        }


def test_self_assessment_orm_and_window_helper_unit() -> None:
    """Testa validações unitárias do ORM SelfAssessmentForm e helper de janela temporal."""
    now = datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
    form = SelfAssessmentForm(
        module_id=uuid4(),
        class_id=uuid4(),
        title="  Autoavaliação Módulo 1  ",
        instructions="  Avalie de 1 a 5 seu domínio técnico.  ",
        opens_at=now - timedelta(days=2),
        closes_at=now + timedelta(days=5),
        is_active=True,
        created_by=uuid4(),
    )
    assert form.title == "Autoavaliação Módulo 1"
    assert form.instructions == "Avalie de 1 a 5 seu domínio técnico."
    assert is_form_window_open(form, reference_now=now) is True

    # Fora da janela (expirado)
    assert (
        is_form_window_open(form, reference_now=now + timedelta(days=10))
        is False
    )

    # Desativado
    form.is_active = False
    assert is_form_window_open(form, reference_now=now) is False

    # Janela inválida no ORM (opens_at >= closes_at)
    with pytest.raises(ValueError, match="estritamente anterior"):
        SelfAssessmentForm(
            module_id=uuid4(),
            class_id=uuid4(),
            title="Questionário Inválido",
            opens_at=now,
            closes_at=now,
            is_active=True,
            created_by=uuid4(),
        )


@pytest.mark.asyncio
async def test_create_self_assessment_form_returns_module_competencies_and_scale_1_to_5(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 1 e Descrição: POST /api/v1/self-assessments/forms cria questionário e retorna module_competencies com escala 1..5."""
    env = _seed_academic_environment(db_session_factory, fast_hasher)
    now = datetime.now(timezone.utc)
    opens_at = (now - timedelta(hours=2)).isoformat()
    closes_at = (now + timedelta(days=7)).isoformat()

    response = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Autoavaliação Prática — Metrologia Módulo 1",
            "instructions": "Responda de 1 a 5 para cada competência prática de bancada.",
            "opens_at": opens_at,
            "closes_at": closes_at,
            "is_active": True,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["module_id"] == str(env["module_with_comps"].id)
    assert body["class_id"] == str(env["class"].id)
    assert body["title"] == "Autoavaliação Prática — Metrologia Módulo 1"
    assert body["is_active"] is True
    assert body["is_open"] is True
    assert body["total_competencies"] == 3

    # Verifica escala 1 a 5 no formulário
    assert body["scale"]["min_level"] == 1
    assert body["scale"]["max_level"] == 5
    assert body["scale"]["options"] == [1, 2, 3, 4, 5]
    assert len(body["scale"]["levels"]) == 5

    # Verifica lista de competências associadas ao módulo (module_competencies) com descrições e escala 1 a 5
    comps = body["competencies"]
    assert len(comps) == 3
    assert body["module_competencies"] == comps
    codes = [c["code"] for c in comps]
    assert codes == ["COMP-MET-01", "COMP-MET-02", "COMP-SEG-01"]
    for comp in comps:
        assert comp["description"] is not None
        assert comp["min_level"] == 1
        assert comp["max_level"] == 5
        assert comp["scale_options"] == [1, 2, 3, 4, 5]
        assert 1 <= comp["required_level"] <= 5


@pytest.mark.asyncio
async def test_create_self_assessment_form_rejects_module_without_competencies(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 1: Criação valida se o módulo possui competências cadastradas e rejeita módulo vazio com 422."""
    env = _seed_academic_environment(db_session_factory, fast_hasher)
    now = datetime.now(timezone.utc)

    response = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_without_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Questionário Módulo Sem Competências",
            "opens_at": (now - timedelta(hours=1)).isoformat(),
            "closes_at": (now + timedelta(days=5)).isoformat(),
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert (
        response.json()["message"]
        == SELF_ASSESSMENT_MODULE_WITHOUT_COMPETENCIES_MESSAGE
    )


@pytest.mark.asyncio
async def test_create_self_assessment_form_validates_opens_at_before_closes_at(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 2: Valida janela de abertura e fechamento (opens_at < closes_at)."""
    env = _seed_academic_environment(db_session_factory, fast_hasher)
    now = datetime.now(timezone.utc)

    # Caso 1: opens_at == closes_at
    same_dt = now.isoformat()
    res_equal = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Janela Igual Inválida",
            "opens_at": same_dt,
            "closes_at": same_dt,
        },
    )
    assert res_equal.status_code == status.HTTP_400_BAD_REQUEST

    # Caso 2: opens_at > closes_at
    res_inverted = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Janela Invertida Inválida",
            "opens_at": (now + timedelta(days=5)).isoformat(),
            "closes_at": (now + timedelta(days=1)).isoformat(),
        },
    )
    assert res_inverted.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_list_pending_forms_for_logged_in_student_and_deadline_reopening(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério 3 e Regra de Negócio: Lista formulários pendentes para o aluno logado e suporta reabertura de prazo pelo professor."""
    env = _seed_academic_environment(db_session_factory, fast_hasher)
    now = datetime.now(timezone.utc)

    # 1. Professor cria Formulário 1 (aberto agora) para o Módulo 1
    res_form_1 = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Autoavaliação Módulo 1 (Aberto)",
            "opens_at": (now - timedelta(days=1)).isoformat(),
            "closes_at": (now + timedelta(days=5)).isoformat(),
            "is_active": True,
        },
    )
    assert res_form_1.status_code == status.HTTP_201_CREATED
    form_1_id = res_form_1.json()["id"]

    # 2. Professor cria Formulário 2 (prazo encerrado no passado) para o Módulo 2
    res_form_2 = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_2_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Autoavaliação Módulo 2 (Prazo Encerrado)",
            "opens_at": (now - timedelta(days=10)).isoformat(),
            "closes_at": (now - timedelta(days=2)).isoformat(),
            "is_active": True,
        },
    )
    assert res_form_2.status_code == status.HTTP_201_CREATED
    form_2_id = res_form_2.json()["id"]

    # 3. Aluno 1 consulta GET /api/v1/classes/{class_id}/self-assessments/forms -> vê apenas o Formulário 1 pendente
    res_student_list = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
    )
    assert res_student_list.status_code == status.HTTP_200_OK
    list_body = res_student_list.json()
    assert list_body["pending_count"] == 1
    assert list_body["total"] == 1
    assert len(list_body["forms"]) == 1
    assert list_body["forms"][0]["id"] == form_1_id
    assert list_body["forms"][0]["is_pending_for_current_student"] is True
    assert list_body["forms"][0]["is_completed_by_current_student"] is False
    assert list_body["forms"][0]["answered_competencies_count"] == 0
    assert len(list_body["forms"][0]["competencies"]) == 3

    # 4. Professor reabre o prazo do Formulário 2 (PATCH /api/v1/self-assessments/forms/{form_id})
    reopen_response = await client.patch(
        f"/api/v1/self-assessments/forms/{form_2_id}",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "title": "Autoavaliação Módulo 2 (Prazo Reaberto)",
            "closes_at": (now + timedelta(days=4)).isoformat(),
            "is_active": True,
        },
    )
    assert reopen_response.status_code == status.HTTP_200_OK
    assert reopen_response.json()["is_open"] is True
    assert reopen_response.json()["title"] == "Autoavaliação Módulo 2 (Prazo Reaberto)"

    # 5. Também suporta reabertura via POST com reopen_if_exists=True
    reopen_post_res = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={
            "module_id": str(env["module_2_with_comps"].id),
            "class_id": str(env["class"].id),
            "title": "Autoavaliação Módulo 2 (Prazo Reaberto via POST)",
            "opens_at": (now - timedelta(days=1)).isoformat(),
            "closes_at": (now + timedelta(days=6)).isoformat(),
            "is_active": True,
            "reopen_if_exists": True,
        },
    )
    assert reopen_post_res.status_code == status.HTTP_201_CREATED
    assert reopen_post_res.json()["id"] == form_2_id

    # 6. Agora o Aluno 1 vê os 2 formulários pendentes
    res_student_after_reopen = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
    )
    assert res_student_after_reopen.status_code == status.HTTP_200_OK
    assert res_student_after_reopen.json()["pending_count"] == 2
    assert len(res_student_after_reopen.json()["forms"]) == 2

    # 7. Simula que o Aluno 1 respondeu todas as 3 competências do Formulário 1
    with db_session_factory() as session:
        for comp in env["competencies"]:
            session.add(
                StudentSelfAssessment(
                    form_id=UUID(form_1_id),
                    student_id=env["student_1"].id,
                    competency_id=comp.id,
                    perceived_level=4,
                    confidence_score=4,
                    difficulty_notes="Domínio adequado em bancada.",
                )
            )
        session.commit()

    # 8. Aluno 1 consulta formulários pendentes -> Formulário 1 deixa de ser pendente, restando apenas Formulário 2
    res_student_1_after_submit = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
    )
    assert res_student_1_after_submit.status_code == status.HTTP_200_OK
    body_s1 = res_student_1_after_submit.json()
    assert body_s1["pending_count"] == 1
    assert len(body_s1["forms"]) == 1
    assert body_s1["forms"][0]["id"] == form_2_id

    # 9. Aluno 1 pode consultar incluindo concluídos (include_completed=true) e ver suas próprias notas sem vazar para Aluno 2
    res_student_1_all = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms?include_completed=true",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
    )
    assert res_student_1_all.status_code == status.HTTP_200_OK
    forms_s1_all = res_student_1_all.json()["forms"]
    assert len(forms_s1_all) == 2
    completed_form = next(f for f in forms_s1_all if f["id"] == form_1_id)
    assert completed_form["is_completed_by_current_student"] is True
    assert completed_form["is_pending_for_current_student"] is False
    assert completed_form["answered_competencies_count"] == 3
    assert completed_form["competencies"][0]["is_answered"] is True
    assert completed_form["competencies"][0]["student_perceived_level"] == 4

    # 10. Aluno 2 (que ainda não respondeu) continua vendo os 2 formulários pendentes e sem dados do Aluno 1
    res_student_2 = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['student_2_token']}"},
    )
    assert res_student_2.status_code == status.HTTP_200_OK
    body_s2 = res_student_2.json()
    assert body_s2["pending_count"] == 2
    form_1_for_s2 = next(f for f in body_s2["forms"] if f["id"] == form_1_id)
    assert form_1_for_s2["answered_competencies_count"] == 0
    assert form_1_for_s2["competencies"][0]["is_answered"] is False
    assert form_1_for_s2["competencies"][0]["student_perceived_level"] is None


@pytest.mark.asyncio
async def test_self_assessment_forms_rbac_and_closed_class_guard(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida RBAC (aluno não cria form, professor não alocado recebe 403, aluno externo recebe 403) e bloqueio BE-029 em turma encerrada."""
    env = _seed_academic_environment(db_session_factory, fast_hasher)
    now = datetime.now(timezone.utc)
    valid_payload = {
        "module_id": str(env["module_with_comps"].id),
        "class_id": str(env["class"].id),
        "title": "Autoavaliação RBAC",
        "opens_at": (now - timedelta(hours=1)).isoformat(),
        "closes_at": (now + timedelta(days=3)).isoformat(),
    }

    # 1. Estudante não pode criar formulário (403)
    res_student_create = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['student_1_token']}"},
        json=valid_payload,
    )
    assert res_student_create.status_code == status.HTTP_403_FORBIDDEN

    # 2. Professor não alocado na turma/disciplina recebe 403 ao criar ou listar
    res_other_teacher_create = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['other_teacher_token']}"},
        json=valid_payload,
    )
    assert res_other_teacher_create.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_other_teacher_create.json()["message"]
        == SELF_ASSESSMENT_TEACHER_FORBIDDEN_MESSAGE
    )

    res_other_teacher_list = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['other_teacher_token']}"},
    )
    assert res_other_teacher_list.status_code == status.HTTP_403_FORBIDDEN

    # 3. Estudante não matriculado na turma recebe 403 ao listar formulários da turma
    res_outsider_student = await client.get(
        f"/api/v1/classes/{env['class'].id}/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['outsider_student_token']}"},
    )
    assert res_outsider_student.status_code == status.HTTP_403_FORBIDDEN
    assert (
        res_outsider_student.json()["message"]
        == SELF_ASSESSMENT_STUDENT_NOT_ENROLLED_MESSAGE
    )

    # 4. Coordenador pode criar e listar formulários em qualquer turma ativa
    res_coord_create = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['coordinator_token']}"},
        json=valid_payload,
    )
    assert res_coord_create.status_code == status.HTTP_201_CREATED
    created_form_id = res_coord_create.json()["id"]

    # 5. Quando a turma é encerrada (COMPLETED), POST e PATCH são bloqueados por check_class_is_active (BE-029)
    with db_session_factory() as session:
        cls = AcademicClassRepository(session=session).get_by_id(env["class"].id)
        assert cls is not None
        cls.status = ClassStatus.COMPLETED
        session.add(cls)
        session.commit()

    res_closed_post = await client.post(
        "/api/v1/self-assessments/forms",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json=valid_payload,
    )
    assert res_closed_post.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert res_closed_post.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE

    res_closed_patch = await client.patch(
        f"/api/v1/self-assessments/forms/{created_form_id}",
        headers={"Authorization": f"Bearer {env['teacher_token']}"},
        json={"closes_at": (now + timedelta(days=10)).isoformat()},
    )
    assert res_closed_patch.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert res_closed_patch.json()["error"] == CLASS_PERIOD_CLOSED_ERROR_CODE
