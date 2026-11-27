"""Testes unitários e de integração para Abertura e Consulta de Solicitações de Apoio Confidenciais pelo Aluno (BE-043)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
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
    ChatMessage,
    Enrollment,
    HelpRequest,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import (
    ClassStatus,
    EnrollmentStatus,
    HelpRequestCategory,
    HelpRequestStatus,
    Shift,
    UserRole,
)
from app.schemas.help_request import (
    HelpRequestCreateSchema,
    HelpRequestListQueryParams,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.help_request_service import (
    HELP_REQUEST_CLASS_NOT_FOUND_MESSAGE,
    HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE,
    HELP_REQUEST_MODULE_SUBJECT_MISMATCH_MESSAGE,
    HELP_REQUEST_STUDENT_NOT_ENROLLED_IN_SUBJECT_COURSE_MESSAGE,
    HELP_REQUEST_STUDENT_NO_ACTIVE_ENROLLMENT_MESSAGE,
    HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE,
    HELP_REQUEST_TEACHER_CLASS_FORBIDDEN_MESSAGE,
    HELP_REQUEST_TEACHER_SUBJECT_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "help_requests_test.db"
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
def help_requests_app(
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
async def client(help_requests_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=help_requests_app)
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
        user = AuthRepository(session=session).create_user(
            email=email,
            password_hash=fast_hasher.hash_password("Senai@2026!Secret"),
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


class TestHelpRequestUnitValidations:
    """Testes unitários de validação Pydantic v2 e ORM para HelpRequest e ChatMessage (BE-043)."""

    def test_create_schema_validates_fields_and_defaults_confidential_true(
        self,
    ) -> None:
        subject_id = uuid4()
        module_id = uuid4()
        valid = HelpRequestCreateSchema(
            subject_id=subject_id,
            module_id=module_id,
            category="practical_difficulty",  # type: ignore[arg-type]
            subject_title="  Dúvida   no   Micrômetro  ",
            description="  Não consigo ajustar o tambor graduado na peça de bancada 02.  ",
        )
        assert valid.subject_id == subject_id
        assert valid.module_id == module_id
        assert valid.category == HelpRequestCategory.PRACTICAL_DIFFICULTY
        assert valid.subject_title == "Dúvida no Micrômetro"
        assert (
            valid.description
            == "Não consigo ajustar o tambor graduado na peça de bancada 02."
        )
        assert valid.is_confidential is True

        # Rejeita assunto curto, descrição curta (<10) e categoria inválida
        with pytest.raises(ValidationError):
            HelpRequestCreateSchema(
                subject_id=subject_id,
                category=HelpRequestCategory.TECHNICAL_DOUBT,
                subject_title="Oi",
                description="Descrição válida com mais de dez caracteres.",
            )

        with pytest.raises(ValidationError):
            HelpRequestCreateSchema(
                subject_id=subject_id,
                category=HelpRequestCategory.TECHNICAL_DOUBT,
                subject_title="Assunto válido",
                description="Curto",
            )

        with pytest.raises(ValidationError):
            HelpRequestCreateSchema(
                subject_id=subject_id,
                category="INVALID_CAT",  # type: ignore[arg-type]
                subject_title="Assunto válido",
                description="Descrição válida com mais de dez caracteres.",
            )

    def test_list_query_params_validation(self) -> None:
        params = HelpRequestListQueryParams(
            page=2,
            limit=25,
            class_id=uuid4(),
            subject_id=uuid4(),
            module_id=uuid4(),
            category="technical_doubt",  # type: ignore[arg-type]
            status="in_progress",  # type: ignore[arg-type]
        )
        assert params.page == 2
        assert params.limit == 25
        assert params.category == HelpRequestCategory.TECHNICAL_DOUBT
        assert params.status == HelpRequestStatus.IN_PROGRESS

        empty_params = HelpRequestListQueryParams(
            category="  ",  # type: ignore[arg-type]
            status="  ",  # type: ignore[arg-type]
        )
        assert empty_params.category is None
        assert empty_params.status is None

        with pytest.raises(ValidationError):
            HelpRequestListQueryParams(page=0)

        with pytest.raises(ValidationError):
            HelpRequestListQueryParams(limit=101)

        with pytest.raises(ValidationError):
            HelpRequestListQueryParams(status="INVALID")  # type: ignore[arg-type]

    def test_orm_models_validation(self) -> None:
        now = datetime(2026, 6, 10, 14, 30, tzinfo=timezone.utc)
        hr = HelpRequest(
            student_id=uuid4(),
            enrollment_id=uuid4(),
            subject_id=uuid4(),
            category=HelpRequestCategory.PERSONAL_PEDAGOGICAL,
            subject_title="  Apoio em Tornearia  ",
            description="  Preciso de orientação prática sobre velocidade de corte.  ",
            is_confidential=True,
            status=HelpRequestStatus.CLOSED,
            resolution_summary="  Mentoria realizada na oficina.  ",
            closed_at=now,
        )
        assert hr.subject_title == "Apoio em Tornearia"
        assert (
            hr.description
            == "Preciso de orientação prática sobre velocidade de corte."
        )
        assert hr.resolution_summary == "Mentoria realizada na oficina."

        with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
            HelpRequest(
                student_id=uuid4(),
                enrollment_id=uuid4(),
                subject_id=uuid4(),
                category=HelpRequestCategory.TECHNICAL_DOUBT,
                subject_title="ab",
                description="Descrição com mais de 10 caracteres.",
            )

        with pytest.raises(ValueError, match="pelo menos 10 caracteres"):
            HelpRequest(
                student_id=uuid4(),
                enrollment_id=uuid4(),
                subject_id=uuid4(),
                category=HelpRequestCategory.TECHNICAL_DOUBT,
                subject_title="Título válido",
                description="123456789",
            )

        msg = ChatMessage(
            help_request_id=uuid4(),
            sender_id=uuid4(),
            message_body="  Olá professor, podemos conversar após a aula?  ",
            is_read=True,
            sent_at=now,
            read_at=now,
        )
        assert msg.message_body == "Olá professor, podemos conversar após a aula?"

        with pytest.raises(ValueError, match="não pode ser vazio"):
            ChatMessage(
                help_request_id=uuid4(),
                sender_id=uuid4(),
                message_body="   ",
            )


@pytest.mark.asyncio
async def test_create_help_request_routes_to_main_teacher_and_validates_business_rules(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/help-requests: HTTP 201, direcionamento automático ao professor titular e regras de validação (BE-043)."""
    main_teacher, main_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.titular043@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Titular Metrologia",
        registration_number="PROF-043-MAIN",
    )
    aux_teacher, _aux_teacher_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.aux043@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Auxiliar Metrologia",
        registration_number="PROF-043-AUX",
    )
    _coord, coord_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord043@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coordenador 043",
        registration_number="COORD-043",
    )
    student_a, student_a_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.a043@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Solicitante A",
        registration_number="ALU-043-A",
    )
    _student_no_enroll, student_no_enroll_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno.semmat043@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno Sem Matrícula",
        registration_number="ALU-043-NONE",
    )

    with db_session_factory() as session:
        course_mec = CourseRepository(session).create(
            code="TEC-MEC-043",
            name="Técnico em Mecânica",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        course_ele = CourseRepository(session).create(
            code="TEC-ELE-043",
            name="Técnico em Eletrotécnica",
            description="Outro curso",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course_mec.id,
            code="MEC-2026-043A",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subj_met = SubjectRepository(session).create(
            course_id=course_mec.id,
            code="MET-043",
            name="Metrologia Dimensional",
            workload_hours=60,
            is_active=True,
        )
        subj_tor = SubjectRepository(session).create(
            course_id=course_mec.id,
            code="TOR-043",
            name="Tornearia Mecânica",
            workload_hours=80,
            is_active=True,
        )
        subj_ele = SubjectRepository(session).create(
            course_id=course_ele.id,
            code="ELE-043",
            name="Comandos Elétricos",
            workload_hours=60,
            is_active=True,
        )
        mod_met_1 = LearningModuleRepository(session).create(
            subject_id=subj_met.id,
            title="Paquímetro e Micrômetro",
            order_index=1,
            description="Medição centesimal",
            practical_hours=20,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("7.00"),
        )
        mod_tor_1 = LearningModuleRepository(session).create(
            subject_id=subj_tor.id,
            title="Faceamento e Cilindramento",
            order_index=1,
            description="Operação de torno",
            practical_hours=30,
            module_weight=Decimal("1.00"),
            passing_score=Decimal("7.00"),
        )
        enrollment_a = Enrollment(
            student_id=student_a.id,
            class_id=class_a.id,
            status=EnrollmentStatus.ACTIVE,
        )
        session.add_all(
            [
                enrollment_a,
                # Professor auxiliar e professor titular na mesma disciplina/turma: deve priorizar is_main_teacher=True
                TeacherAssignment(
                    teacher_id=aux_teacher.id,
                    class_id=class_a.id,
                    subject_id=subj_met.id,
                    is_main_teacher=False,
                ),
                TeacherAssignment(
                    teacher_id=main_teacher.id,
                    class_id=class_a.id,
                    subject_id=subj_met.id,
                    is_main_teacher=True,
                ),
            ]
        )
        session.commit()
        enrollment_a_id = enrollment_a.id

    stu_a_headers = {"Authorization": f"Bearer {student_a_token}"}
    stu_none_headers = {"Authorization": f"Bearer {student_no_enroll_token}"}
    teacher_headers = {"Authorization": f"Bearer {main_teacher_token}"}
    coord_headers = {"Authorization": f"Bearer {coord_token}"}

    # 1. Sem token -> 401; Professor ou Coordenador tentando abrir help_request -> 403
    assert (
        await client.post(
            "/api/v1/help-requests",
            json={
                "subject_id": str(subj_met.id),
                "category": "PRACTICAL_DIFFICULTY",
                "subject_title": "Dúvida sem login",
                "description": "Tentativa sem token de autenticação.",
            },
        )
    ).status_code == status.HTTP_401_UNAUTHORIZED

    assert (
        await client.post(
            "/api/v1/help-requests",
            headers=teacher_headers,
            json={
                "subject_id": str(subj_met.id),
                "category": "PRACTICAL_DIFFICULTY",
                "subject_title": "Tentativa por professor",
                "description": "Professor não abre pedido de ajuda de aluno.",
            },
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    assert (
        await client.post(
            "/api/v1/help-requests",
            headers=coord_headers,
            json={
                "subject_id": str(subj_met.id),
                "category": "PRACTICAL_DIFFICULTY",
                "subject_title": "Tentativa por coordenador",
                "description": "Coordenador não abre pedido de ajuda de aluno.",
            },
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    # 2. Disciplina inexistente -> 404; Módulo inexistente -> 404; Módulo de outra disciplina -> 422
    not_found_subj = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(uuid4()),
            "category": "TECHNICAL_DOUBT",
            "subject_title": "Disciplina não existe",
            "description": "Relato detalhado com mais de dez caracteres.",
        },
    )
    assert not_found_subj.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_subj.json()["message"] == HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE

    not_found_mod = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(subj_met.id),
            "module_id": str(uuid4()),
            "category": "TECHNICAL_DOUBT",
            "subject_title": "Módulo não existe",
            "description": "Relato detalhado com mais de dez caracteres.",
        },
    )
    assert not_found_mod.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_mod.json()["message"] == HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE

    mismatch_mod = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(subj_met.id),
            "module_id": str(mod_tor_1.id),
            "category": "PRACTICAL_DIFFICULTY",
            "subject_title": "Módulo de outra disciplina",
            "description": "Módulo de tornearia enviado junto com disciplina de metrologia.",
        },
    )
    assert mismatch_mod.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        mismatch_mod.json()["message"] == HELP_REQUEST_MODULE_SUBJECT_MISMATCH_MESSAGE
    )

    # 3. Estudante sem nenhuma matrícula ativa -> 403; Estudante matriculado em outro curso -> 403
    no_enroll_res = await client.post(
        "/api/v1/help-requests",
        headers=stu_none_headers,
        json={
            "subject_id": str(subj_met.id),
            "category": "TECHNICAL_DOUBT",
            "subject_title": "Sem matrícula ativa",
            "description": "Aluno ainda não matriculado em nenhuma turma.",
        },
    )
    assert no_enroll_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        no_enroll_res.json()["message"]
        == HELP_REQUEST_STUDENT_NO_ACTIVE_ENROLLMENT_MESSAGE
    )

    wrong_course_res = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(subj_ele.id),
            "category": "TECHNICAL_DOUBT",
            "subject_title": "Disciplina de outro curso",
            "description": "Aluno de Mecânica tentando abrir chamado em Eletrotécnica.",
        },
    )
    assert wrong_course_res.status_code == status.HTTP_403_FORBIDDEN
    assert (
        wrong_course_res.json()["message"]
        == HELP_REQUEST_STUDENT_NOT_ENROLLED_IN_SUBJECT_COURSE_MESSAGE
    )

    # 4. Criação bem-sucedida (HTTP 201 Created): is_confidential default True + direciona ao professor titular
    create_res = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(subj_met.id),
            "module_id": str(mod_met_1.id),
            "category": "PRACTICAL_DIFFICULTY",
            "subject_title": "Dificuldade na leitura do nônio do micrômetro externo",
            "description": "Tenho receio de apertar demais a catraca do micrômetro e errar a tolerância centesimal.",
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    body = create_res.json()
    assert body["student_id"] == str(student_a.id)
    assert body["enrollment_id"] == str(enrollment_a_id)
    assert body["class_id"] == str(class_a.id)
    assert body["subject_id"] == str(subj_met.id)
    assert body["module_id"] == str(mod_met_1.id)
    assert body["assigned_teacher_id"] == str(main_teacher.id)
    assert body["assigned_teacher"]["full_name"] == "Prof. Titular Metrologia"
    assert body["category"] == "PRACTICAL_DIFFICULTY"
    assert body["is_confidential"] is True
    assert body["status"] == "OPEN"
    assert body["closed_at"] is None
    assert body["student"]["full_name"] == "Aluno Solicitante A"
    assert body["academic_class"]["code"] == "MEC-2026-043A"
    assert body["subject"]["code"] == "MET-043"
    assert body["module"]["title"] == "Paquímetro e Micrômetro"
    assert body["unread_messages_count"] == 0
    assert body["messages"] == []

    # 5. Criação em disciplina da turma ainda sem professor titular alocado (assigned_teacher_id = None, status OPEN)
    unassigned_subj_res = await client.post(
        "/api/v1/help-requests",
        headers=stu_a_headers,
        json={
            "subject_id": str(subj_tor.id),
            "category": "PERSONAL_PEDAGOGICAL",
            "subject_title": "Orientação sobre preparação para oficina de torno",
            "description": "Gostaria de apoio pedagógico antes do início das aulas práticas de tornearia.",
            "is_confidential": True,
        },
    )
    assert unassigned_subj_res.status_code == status.HTTP_201_CREATED
    assert unassigned_subj_res.json()["assigned_teacher_id"] is None
    assert unassigned_subj_res.json()["assigned_teacher"] is None


@pytest.mark.asyncio
async def test_list_help_requests_strict_confidentiality_and_teacher_subject_isolation(
    client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/help-requests: proteção anti-exposição entre estudantes e visibilidade por disciplina do professor (BE-043)."""
    teacher_met, teacher_met_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.met043@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Metrologia",
        registration_number="PROF-043-MET",
    )
    teacher_tor, teacher_tor_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="prof.tor043@senai.br",
        role=UserRole.TEACHER,
        full_name="Prof. Tornearia",
        registration_number="PROF-043-TOR",
    )
    _coord, coord_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="coord.list043@senai.br",
        role=UserRole.COORDINATOR,
        full_name="Coordenador Geral",
        registration_number="COORD-043-L",
    )
    student_1, student_1_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno1.043@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno 01 Confidencial",
        registration_number="ALU-043-01",
    )
    student_2, student_2_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno2.043@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno 02 Colega da Mesma Turma",
        registration_number="ALU-043-02",
    )
    _student_3, student_3_token = _seed_user_with_token(
        db_session_factory,
        fast_hasher,
        email="aluno3.043@senai.br",
        role=UserRole.STUDENT,
        full_name="Aluno 03 Sem Pedidos",
        registration_number="ALU-043-03",
    )

    with db_session_factory() as session:
        course = CourseRepository(session).create(
            code="TEC-MEC-043L",
            name="Técnico em Mecânica Industrial",
            description="Curso Técnico SENAI",
            total_hours=1200,
            is_active=True,
        )
        class_a = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-043L1",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        class_b = AcademicClassRepository(session).create(
            course_id=course.id,
            code="MEC-2026-043L2",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 12, 31),
        )
        subj_met = SubjectRepository(session).create(
            course_id=course.id,
            code="MET-043L",
            name="Metrologia",
            workload_hours=60,
            is_active=True,
        )
        subj_tor = SubjectRepository(session).create(
            course_id=course.id,
            code="TOR-043L",
            name="Tornearia",
            workload_hours=80,
            is_active=True,
        )
        session.add_all(
            [
                TeacherAssignment(
                    teacher_id=teacher_met.id,
                    class_id=class_a.id,
                    subject_id=subj_met.id,
                    is_main_teacher=True,
                ),
                TeacherAssignment(
                    teacher_id=teacher_tor.id,
                    class_id=class_a.id,
                    subject_id=subj_tor.id,
                    is_main_teacher=True,
                ),
                Enrollment(
                    student_id=student_1.id,
                    class_id=class_a.id,
                    status=EnrollmentStatus.ACTIVE,
                ),
                Enrollment(
                    student_id=student_2.id,
                    class_id=class_a.id,
                    status=EnrollmentStatus.ACTIVE,
                ),
            ]
        )
        session.commit()

    s1_headers = {"Authorization": f"Bearer {student_1_token}"}
    s2_headers = {"Authorization": f"Bearer {student_2_token}"}
    s3_headers = {"Authorization": f"Bearer {student_3_token}"}
    t_met_headers = {"Authorization": f"Bearer {teacher_met_token}"}
    t_tor_headers = {"Authorization": f"Bearer {teacher_tor_token}"}
    coord_headers = {"Authorization": f"Bearer {coord_token}"}

    # Aluno 1 abre 2 pedidos (um em Metrologia e um em Tornearia)
    hr_s1_met_res = await client.post(
        "/api/v1/help-requests",
        headers=s1_headers,
        json={
            "subject_id": str(subj_met.id),
            "category": "PRACTICAL_DIFFICULTY",
            "subject_title": "Pedido Confidencial Aluno 1 em Metrologia",
            "description": "Dificuldade confidencial do Aluno 1 com medição de peça cilíndrica.",
        },
    )
    assert hr_s1_met_res.status_code == status.HTTP_201_CREATED
    hr_s1_met_id = UUID(hr_s1_met_res.json()["id"])

    hr_s1_tor_res = await client.post(
        "/api/v1/help-requests",
        headers=s1_headers,
        json={
            "subject_id": str(subj_tor.id),
            "category": "TECHNICAL_DOUBT",
            "subject_title": "Pedido Confidencial Aluno 1 em Tornearia",
            "description": "Dúvida confidencial do Aluno 1 sobre escolha de bedame no torno.",
        },
    )
    assert hr_s1_tor_res.status_code == status.HTTP_201_CREATED
    hr_s1_tor_id = UUID(hr_s1_tor_res.json()["id"])

    # Aluno 2 (mesma turma!) abre 1 pedido em Metrologia
    hr_s2_met_res = await client.post(
        "/api/v1/help-requests",
        headers=s2_headers,
        json={
            "subject_id": str(subj_met.id),
            "category": "PERSONAL_PEDAGOGICAL",
            "subject_title": "Pedido Confidencial Aluno 2 em Metrologia",
            "description": "Relato pessoal confidencial do Aluno 2 que o Aluno 1 jamais pode ver.",
        },
    )
    assert hr_s2_met_res.status_code == status.HTTP_201_CREATED
    hr_s2_met_id = UUID(hr_s2_met_res.json()["id"])

    # Simula mensagem enviada pelo professor para Aluno 1 em hr_s1_met_id para testar serialização de chat_messages
    with db_session_factory() as session:
        session.add(
            ChatMessage(
                help_request_id=hr_s1_met_id,
                sender_id=teacher_met.id,
                message_body="Olá Aluno 01, podemos fazer uma mentoria reservada às 10h no Lab 01.",
                is_read=False,
            )
        )
        session.commit()

    # 1. PROTEÇÃO ANTI-EXPOSIÇÃO: Aluno 1 vê estritamente seus 2 pedidos (jamais vê o do Aluno 2 da mesma turma)
    s1_list = await client.get("/api/v1/help-requests", headers=s1_headers)
    assert s1_list.status_code == status.HTTP_200_OK
    s1_data = s1_list.json()
    assert s1_data["total"] == 2
    s1_returned_ids = {UUID(item["id"]) for item in s1_data["data"]}
    assert s1_returned_ids == {hr_s1_met_id, hr_s1_tor_id}
    assert hr_s2_met_id not in s1_returned_ids
    assert all(item["student_id"] == str(student_1.id) for item in s1_data["data"])

    met_item_for_s1 = next(
        item for item in s1_data["data"] if UUID(item["id"]) == hr_s1_met_id
    )
    assert met_item_for_s1["unread_messages_count"] == 1
    assert len(met_item_for_s1["messages"]) == 1
    assert (
        met_item_for_s1["messages"][0]["sender_name"] == "Prof. Metrologia"
    )

    # 2. PROTEÇÃO ANTI-EXPOSIÇÃO: Aluno 2 vê estritamente seu único pedido (jamais vê os do Aluno 1)
    s2_list = await client.get("/api/v1/help-requests", headers=s2_headers)
    assert s2_list.status_code == status.HTTP_200_OK
    s2_data = s2_list.json()
    assert s2_data["total"] == 1
    assert UUID(s2_data["data"][0]["id"]) == hr_s2_met_id
    assert s2_data["data"][0]["student_id"] == str(student_2.id)

    # 3. PROTEÇÃO ANTI-EXPOSIÇÃO: Aluno 3 vê lista vazia
    s3_list = await client.get("/api/v1/help-requests", headers=s3_headers)
    assert s3_list.status_code == status.HTTP_200_OK
    assert s3_list.json()["total"] == 0
    assert s3_list.json()["data"] == []

    # 4. ESCOPO DOCENTE: Professor de Metrologia vê apenas os 2 pedidos de Metrologia (Aluno 1 e Aluno 2)
    t_met_list = await client.get("/api/v1/help-requests", headers=t_met_headers)
    assert t_met_list.status_code == status.HTTP_200_OK
    t_met_data = t_met_list.json()
    assert t_met_data["total"] == 2
    assert {UUID(item["id"]) for item in t_met_data["data"]} == {
        hr_s1_met_id,
        hr_s2_met_id,
    }

    # E para o professor que enviou a mensagem, unread_messages_count dessa mensagem enviada por ele mesmo é 0
    met_item_for_teacher = next(
        item for item in t_met_data["data"] if UUID(item["id"]) == hr_s1_met_id
    )
    assert met_item_for_teacher["unread_messages_count"] == 0

    # 5. ESCOPO DOCENTE: Professor de Tornearia vê apenas o pedido de Tornearia
    t_tor_list = await client.get("/api/v1/help-requests", headers=t_tor_headers)
    assert t_tor_list.status_code == status.HTTP_200_OK
    t_tor_data = t_tor_list.json()
    assert t_tor_data["total"] == 1
    assert UUID(t_tor_data["data"][0]["id"]) == hr_s1_tor_id

    # Professor de Metrologia tentando filtrar por disciplina que não leciona (Tornearia) -> 403
    forbidden_subj_filter = await client.get(
        f"/api/v1/help-requests?subject_id={subj_tor.id}",
        headers=t_met_headers,
    )
    assert forbidden_subj_filter.status_code == status.HTTP_403_FORBIDDEN
    assert (
        forbidden_subj_filter.json()["message"]
        == HELP_REQUEST_TEACHER_SUBJECT_FORBIDDEN_MESSAGE
    )

    # Professor tentando filtrar por turma que não leciona (class_b) -> 403
    forbidden_cls_filter = await client.get(
        f"/api/v1/help-requests?class_id={class_b.id}",
        headers=t_met_headers,
    )
    assert forbidden_cls_filter.status_code == status.HTTP_403_FORBIDDEN
    assert (
        forbidden_cls_filter.json()["message"]
        == HELP_REQUEST_TEACHER_CLASS_FORBIDDEN_MESSAGE
    )

    # 6. Coordenação visualiza todos os 3 pedidos e pode filtrar por categoria/status/disciplina
    coord_list = await client.get("/api/v1/help-requests", headers=coord_headers)
    assert coord_list.status_code == status.HTTP_200_OK
    assert coord_list.json()["total"] == 3

    coord_cat_filter = await client.get(
        "/api/v1/help-requests?category=PERSONAL_PEDAGOGICAL&status=OPEN",
        headers=coord_headers,
    )
    assert coord_cat_filter.status_code == status.HTTP_200_OK
    assert coord_cat_filter.json()["total"] == 1
    assert UUID(coord_cat_filter.json()["data"][0]["id"]) == hr_s2_met_id

    # 7. Filtros com class_id, subject_id ou module_id inexistentes retornam 404
    assert (
        await client.get(
            f"/api/v1/help-requests?class_id={uuid4()}",
            headers=coord_headers,
        )
    ).json()["message"] == HELP_REQUEST_CLASS_NOT_FOUND_MESSAGE

    assert (
        await client.get(
            f"/api/v1/help-requests?subject_id={uuid4()}",
            headers=coord_headers,
        )
    ).json()["message"] == HELP_REQUEST_SUBJECT_NOT_FOUND_MESSAGE

    assert (
        await client.get(
            f"/api/v1/help-requests?module_id={uuid4()}",
            headers=coord_headers,
        )
    ).json()["message"] == HELP_REQUEST_MODULE_NOT_FOUND_MESSAGE
