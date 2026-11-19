"""Testes unitários e de integração para Endpoints de Módulos de Aprendizagem Prática (BE-014)."""

from collections.abc import AsyncIterator, Generator
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import Base, Course, LearningModule, Subject, User
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import UserRole
from app.schemas.learning_module import (
    LearningModuleCreateSchema,
    validate_learning_module_title_pt,
    validate_module_order_index_pt,
    validate_module_weight_pt,
    validate_passing_score_pt,
    validate_practical_hours_pt,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.learning_module_service import (
    LEARNING_MODULE_INACTIVE_SUBJECT_MESSAGE,
    LEARNING_MODULE_ORDER_CONFLICT_MESSAGE,
    LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE,
    LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE,
)


@pytest.fixture
def db_engine() -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite em memória isolada para cada teste."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session_factory(db_engine: sa.Engine) -> sessionmaker[Session]:
    """Cria a fábrica de sessões SQLAlchemy acoplada à engine isolada."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def modules_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância da aplicação FastAPI com dependências de banco e hasher sobrescritas."""
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
async def modules_client(modules_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=modules_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
) -> tuple[User, str]:
    """Cria um usuário persistido no banco de testes e gera seu Access Token JWT."""
    with session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=True,
            profile_data=UserProfileCreateSchema(
                full_name=f"Usuário {role.value} {suffix}",
                registration_number=f"SENAI-{role.value[:3]}-{suffix.upper()}",
                phone="(11) 98888-7777",
            ),
        )
    token = create_access_token(
        subject=user.id,
        email=user.email,
        role=user.role,
    )
    return user, token


def _create_course_in_db(
    session_factory: sessionmaker[Session],
    *,
    code: str = "TEC-MEC-01",
    name: str = "Técnico em Mecânica Industrial",
    total_hours: int = 1200,
    is_active: bool = True,
) -> Course:
    """Helper para persistir um curso técnico diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description="Formação técnica em usinagem, tornearia e metrologia.",
            total_hours=total_hours,
            is_active=is_active,
        )


def _create_subject_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str,
    name: str,
    workload_hours: int = 80,
    is_active: bool = True,
) -> Subject:
    """Helper para persistir uma disciplina técnica diretamente via repositório."""
    with session_factory() as session:
        repo = SubjectRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            name=name,
            workload_hours=workload_hours,
            syllabus="Ementa teórico-prática SENAI.",
            is_active=is_active,
        )


def _create_learning_module_in_db(
    session_factory: sessionmaker[Session],
    *,
    subject_id: UUID,
    title: str,
    order_index: int,
    practical_hours: int = 40,
    description: str | None = None,
    module_weight: Decimal = Decimal("1.00"),
    passing_score: Decimal = Decimal("6.00"),
) -> LearningModule:
    """Helper para persistir um módulo prático diretamente via repositório."""
    with session_factory() as session:
        repo = LearningModuleRepository(session=session)
        return repo.create(
            subject_id=subject_id,
            title=title,
            order_index=order_index,
            practical_hours=practical_hours,
            description=description,
            module_weight=module_weight,
            passing_score=passing_score,
        )


def _create_auxiliary_teacher_assignments_table(engine: sa.Engine) -> sa.Table:
    """Cria tabela auxiliar 'teacher_assignments' em MetaData separada para validar RBAC docente."""
    aux_metadata = sa.MetaData()
    ta_table = sa.Table(
        "teacher_assignments",
        aux_metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("teacher_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("class_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subject_id", sa.Uuid(as_uuid=True), nullable=False),
    )
    aux_metadata.create_all(bind=engine)
    return ta_table


def test_learning_module_orm_validations_and_db_constraints(
    db_session_factory: sessionmaker[Session],
) -> None:
    """Valida restrições unitárias ORM e constraints relacionais no banco (uq e check)."""
    course = _create_course_in_db(db_session_factory)
    subject_tornearia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-TOR-01",
        name="Usinagem e Tornearia",
        workload_hours=120,
    )
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )

    valid_module = LearningModule(
        subject_id=subject_tornearia.id,
        title="  Módulo de Tornearia Cilíndrica  ",
        order_index=1,
        description="  Operação de torno convencional e faceamento.  ",
        practical_hours=40,
        module_weight=Decimal("1.5"),
        passing_score=Decimal("7.5"),
    )
    assert valid_module.title == "Módulo de Tornearia Cilíndrica"
    assert valid_module.description == "Operação de torno convencional e faceamento."
    assert valid_module.module_weight == Decimal("1.50")
    assert valid_module.passing_score == Decimal("7.50")

    blank_desc = LearningModule(
        subject_id=subject_tornearia.id,
        title="Módulo de Segurança",
        order_index=2,
        description="   ",
        practical_hours=0,
    )
    assert blank_desc.description is None

    with pytest.raises(ValueError, match="entre 3 e 120 caracteres"):
        LearningModule(
            subject_id=subject_tornearia.id,
            title="AB",
            order_index=1,
            practical_hours=10,
        )

    with pytest.raises(ValueError, match="entre 3 e 120 caracteres"):
        LearningModule(
            subject_id=subject_tornearia.id,
            title="X" * 121,
            order_index=1,
            practical_hours=10,
        )

    for invalid_order in (0, -1, True):
        with pytest.raises(ValueError, match="order_index"):
            LearningModule(
                subject_id=subject_tornearia.id,
                title="Módulo Válido",
                order_index=invalid_order,  # type: ignore[arg-type]
                practical_hours=10,
            )

    for invalid_hours in (-1, -20, True):
        with pytest.raises(ValueError, match="practical_hours"):
            LearningModule(
                subject_id=subject_tornearia.id,
                title="Módulo Válido",
                order_index=1,
                practical_hours=invalid_hours,  # type: ignore[arg-type]
            )

    for invalid_score in (Decimal("-0.01"), Decimal("10.01"), True, float("nan")):
        with pytest.raises(ValueError, match="passing_score"):
            LearningModule(
                subject_id=subject_tornearia.id,
                title="Módulo Válido",
                order_index=1,
                practical_hours=10,
                passing_score=invalid_score,  # type: ignore[arg-type]
            )

    for invalid_weight in (Decimal("0.00"), Decimal("-1.00"), Decimal("100.00"), True):
        with pytest.raises(ValueError, match="module_weight"):
            LearningModule(
                subject_id=subject_tornearia.id,
                title="Módulo Válido",
                order_index=1,
                practical_hours=10,
                module_weight=invalid_weight,  # type: ignore[arg-type]
            )

    # Persistência válida e unicidade (subject_id, order_index)
    with db_session_factory() as session:
        session.add(valid_module)
        session.commit()

    with db_session_factory() as session:
        dup_order = LearningModule(
            subject_id=subject_tornearia.id,
            title="Módulo Duplicado na Ordem",
            order_index=1,
            practical_hours=20,
        )
        session.add(dup_order)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Mesmo order_index em outra disciplina é permitido
    with db_session_factory() as session:
        other_subject_module = LearningModule(
            subject_id=subject_metrologia.id,
            title="Metrologia com Paquímetro",
            order_index=1,
            practical_hours=24,
        )
        session.add(other_subject_module)
        session.commit()

    # Constraints CHECK SQL no nível do banco de dados
    invalid_sql_rows = [
        {"order_index": 0, "practical_hours": 10, "module_weight": 1.0, "passing_score": 6.0},
        {"order_index": 5, "practical_hours": -1, "module_weight": 1.0, "passing_score": 6.0},
        {"order_index": 6, "practical_hours": 10, "module_weight": 0.0, "passing_score": 6.0},
        {"order_index": 7, "practical_hours": 10, "module_weight": 1.0, "passing_score": -0.5},
        {"order_index": 8, "practical_hours": 10, "module_weight": 1.0, "passing_score": 10.5},
    ]
    for row in invalid_sql_rows:
        with db_session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    sa.text(
                        "INSERT INTO learning_modules "
                        "(id, subject_id, title, order_index, practical_hours, module_weight, passing_score) "
                        "VALUES (:id, :subject_id, :title, :order_index, :practical_hours, :module_weight, :passing_score)"
                    ),
                    {
                        "id": str(uuid4()).replace("-", ""),
                        "subject_id": str(subject_tornearia.id).replace("-", ""),
                        "title": "Módulo SQL Check",
                        **row,
                    },
                )
                session.commit()
            session.rollback()


def test_pydantic_validators_for_learning_modules() -> None:
    """Valida regras Pydantic de passing_score (0.00 a 10.00), peso, horas e título."""
    assert validate_learning_module_title_pt("  Tornearia   Cônica  ") == "Tornearia Cônica"
    assert validate_module_order_index_pt("3") == 3
    assert validate_practical_hours_pt(0) == 0
    assert validate_practical_hours_pt("24") == 24
    assert validate_passing_score_pt(0) == Decimal("0.00")
    assert validate_passing_score_pt(0.00) == Decimal("0.00")
    assert validate_passing_score_pt(6) == Decimal("6.00")
    assert validate_passing_score_pt(6.5) == Decimal("6.50")
    assert validate_passing_score_pt("7.25") == Decimal("7.25")
    assert validate_passing_score_pt(10) == Decimal("10.00")
    assert validate_passing_score_pt("10.00") == Decimal("10.00")
    assert validate_module_weight_pt("2.5") == Decimal("2.50")

    for invalid_score in (-0.01, -1, 10.01, 15, 6.125, True, False, "abc", float("nan"), float("inf")):
        with pytest.raises(Exception):
            validate_passing_score_pt(invalid_score)

    for invalid_weight in (0, 0.00, -1, 100.00, 1.234, True, "abc"):
        with pytest.raises(Exception):
            validate_module_weight_pt(invalid_weight)

    for invalid_hours in (-1, -10, True, 12.5, "abc"):
        with pytest.raises(Exception):
            validate_practical_hours_pt(invalid_hours)

    for invalid_order in (0, -2, True, 1.5, "abc"):
        with pytest.raises(Exception):
            validate_module_order_index_pt(invalid_order)

    for invalid_title in ("AB", "Y" * 121, "<script>alert(1)</script>"):
        with pytest.raises(Exception):
            validate_learning_module_title_pt(invalid_title)

    schema = LearningModuleCreateSchema(
        subject_id=uuid4(),
        title="  Metrologia   com   Micrômetro  ",
        practical_hours=24,
        passing_score="7.5",  # type: ignore[arg-type]
    )
    assert schema.title == "Metrologia com Micrômetro"
    assert schema.order_index is None
    assert schema.module_weight == Decimal("1.00")
    assert schema.passing_score == Decimal("7.50")


async def test_learning_modules_rbac_and_contextual_teacher_assignment(
    modules_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Permissão restrita a docentes alocados na disciplina e coordenadores."""
    course = _create_course_in_db(db_session_factory)
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )
    subject_tornearia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-TOR-01",
        name="Usinagem e Tornearia",
        workload_hours=120,
    )
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_metrologia.id,
        title="Leitura com Paquímetro",
        order_index=1,
        practical_hours=20,
    )

    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="stu"
    )
    teacher_user, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="tch"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="adm"
    )

    post_metrologia = {
        "subject_id": str(subject_metrologia.id),
        "title": "Metrologia com Micrômetro",
        "practical_hours": 24,
        "passing_score": "7.00",
    }
    post_tornearia = {
        "subject_id": str(subject_tornearia.id),
        "title": "Módulo de Tornearia Cilíndrica",
        "practical_hours": 40,
        "passing_score": "6.50",
    }

    # 1. Sem token -> 401; STUDENT -> 403
    for method, url, body in (
        ("GET", f"/api/v1/subjects/{subject_metrologia.id}/modules", None),
        ("POST", "/api/v1/modules", post_metrologia),
    ):
        unauth_res = await modules_client.request(method, url, json=body)
        assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

        student_res = await modules_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_res.status_code == status.HTTP_403_FORBIDDEN
        assert student_res.json()["message"] == "Acesso não autorizado para seu perfil"

    # 2. TEACHER sem tabela teacher_assignments -> 403 em ambas as rotas
    teacher_no_table_get = await modules_client.get(
        f"/api/v1/subjects/{subject_metrologia.id}/modules",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_no_table_get.status_code == status.HTTP_403_FORBIDDEN
    assert teacher_no_table_get.json()["message"] == LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE

    teacher_no_table_post = await modules_client.post(
        "/api/v1/modules",
        json=post_metrologia,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_no_table_post.status_code == status.HTTP_403_FORBIDDEN
    assert teacher_no_table_post.json()["message"] == LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE

    # 3. Cria tabela teacher_assignments alocando o docente apenas em Metrologia
    ta_table = _create_auxiliary_teacher_assignments_table(db_engine)
    with db_session_factory() as session:
        session.execute(
            ta_table.insert().values(
                id=uuid4(),
                teacher_id=teacher_user.id,
                class_id=uuid4(),
                subject_id=subject_metrologia.id,
            )
        )
        session.commit()

    # Docente alocado em Metrologia consegue GET (200) e POST (201)
    teacher_ok_get = await modules_client.get(
        f"/api/v1/subjects/{subject_metrologia.id}/modules",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_ok_get.status_code == status.HTTP_200_OK
    assert teacher_ok_get.json()["total"] == 1

    teacher_ok_post = await modules_client.post(
        "/api/v1/modules",
        json=post_metrologia,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_ok_post.status_code == status.HTTP_201_CREATED
    assert teacher_ok_post.json()["order_index"] == 2

    # Docente NÃO alocado em Tornearia recebe 403 em GET e POST
    teacher_denied_get = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_denied_get.status_code == status.HTTP_403_FORBIDDEN
    assert teacher_denied_get.json()["message"] == LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE

    teacher_denied_post = await modules_client.post(
        "/api/v1/modules",
        json=post_tornearia,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_denied_post.status_code == status.HTTP_403_FORBIDDEN
    assert teacher_denied_post.json()["message"] == LEARNING_MODULE_TEACHER_FORBIDDEN_MESSAGE

    # 4. COORDINATOR e ADMIN possuem acesso livre sem registro em teacher_assignments
    coord_post = await modules_client.post(
        "/api/v1/modules",
        json=post_tornearia,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert coord_post.status_code == status.HTTP_201_CREATED

    admin_get = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_get.status_code == status.HTTP_200_OK
    assert admin_get.json()["total"] == 1


async def test_create_learning_module_success_defaults_and_mechanics_metrology_flow(
    modules_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """DoD: Testa POST /api/v1/modules com módulos práticos de Mecânica (Tornearia) e Metrologia."""
    course = _create_course_in_db(db_session_factory)
    subject_tornearia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-TOR-01",
        name="Processos de Tornearia Mecânica",
        workload_hours=120,
    )
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="c1"
    )

    # 1. Criação explícita com passing_score, module_weight e descrição multilinha
    desc = "Bancada Torno Nardini 300.\nExecutar desbaste e acabamento em eixo Ø25mm H7."
    res_tornearia = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(subject_tornearia.id),
            "title": "  Módulo de   Tornearia Cilíndrica  ",
            "order_index": 1,
            "description": f"  {desc}  ",
            "practical_hours": 40,
            "module_weight": "2.00",
            "passing_score": 7.5,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_tornearia.status_code == status.HTTP_201_CREATED
    body_t = res_tornearia.json()
    UUID(body_t["id"])
    assert body_t["subject_id"] == str(subject_tornearia.id)
    assert body_t["title"] == "Módulo de Tornearia Cilíndrica"
    assert body_t["order_index"] == 1
    assert body_t["description"] == desc
    assert body_t["practical_hours"] == 40
    assert body_t["module_weight"] == "2.00"
    assert body_t["passing_score"] == "7.50"
    assert body_t["subject"] == {
        "id": str(subject_tornearia.id),
        "course_id": str(course.id),
        "code": "USN-TOR-01",
        "name": "Processos de Tornearia Mecânica",
        "workload_hours": 120,
        "is_active": True,
    }

    # 2. Criação omitindo order_index, passing_score e module_weight (usa defaults e sequencial automático)
    res_auto_order = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(subject_tornearia.id),
            "title": "Tornearia Cônica e Rosqueamento",
            "practical_hours": 0,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_auto_order.status_code == status.HTTP_201_CREATED
    body_auto = res_auto_order.json()
    assert body_auto["order_index"] == 2
    assert body_auto["practical_hours"] == 0
    assert body_auto["module_weight"] == "1.00"
    assert body_auto["passing_score"] == "6.00"

    # 3. Limites inclusivos válidos de passing_score (0.00 e 10.00) em Metrologia
    res_min_score = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(subject_metrologia.id),
            "title": "Metrologia Básica com Paquímetro",
            "order_index": 1,
            "practical_hours": 16,
            "passing_score": "0.00",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_min_score.status_code == status.HTTP_201_CREATED
    assert res_min_score.json()["passing_score"] == "0.00"

    res_max_score = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(subject_metrologia.id),
            "title": "Metrologia com Micrômetro Centesimal",
            "order_index": 2,
            "practical_hours": 24,
            "passing_score": 10.0,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_max_score.status_code == status.HTTP_201_CREATED
    assert res_max_score.json()["passing_score"] == "10.00"

    with db_session_factory() as session:
        persisted = session.scalar(
            select(LearningModule).where(LearningModule.id == UUID(body_t["id"]))
        )
        assert persisted is not None
        assert persisted.passing_score == Decimal("7.50")
        assert persisted.module_weight == Decimal("2.00")


@pytest.mark.parametrize(
    "invalid_passing_score",
    [-0.01, -5, 10.01, 12, 6.125, True, False, "nota", ""],
)
async def test_create_learning_module_rejects_invalid_passing_score_with_400(
    modules_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    invalid_passing_score: Any,
) -> None:
    """Critério de Aceitação: Validação Pydantic de passing_score estritamente entre 0.00 e 10.00."""
    course = _create_course_in_db(db_session_factory)
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-01",
        name="Metrologia Dimensional",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="ps"
    )

    response = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(subject.id),
            "title": "Metrologia com Súbito",
            "practical_hours": 20,
            "passing_score": invalid_passing_score,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert any(item["field"] == "passing_score" for item in body["details"])


@pytest.mark.parametrize(
    "invalid_payload_override",
    [
        {"title": "AB"},
        {"title": "<script>alert(1)</script>"},
        {"description": "<iframe src='x'></iframe>"},
        {"order_index": 0},
        {"order_index": -1},
        {"order_index": False},
        {"practical_hours": -1},
        {"practical_hours": True},
        {"module_weight": 0},
        {"module_weight": -1.5},
        {"module_weight": 100.00},
        {"module_weight": 1.234},
        {"subject_id": "uuid-invalido"},
        {"extra_field": "nao-permitido"},
    ],
)
async def test_create_learning_module_rejects_invalid_or_unsafe_payload_with_400(
    modules_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    invalid_payload_override: dict[str, Any],
) -> None:
    """Garante HTTP 400 para campos inválidos, horas negativas, peso inválido, XSS e extras."""
    course = _create_course_in_db(db_session_factory)
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-01",
        name="Usinagem Convencional",
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="inv"
    )

    payload: dict[str, Any] = {
        "subject_id": str(subject.id),
        "title": "Módulo de Tornearia",
        "practical_hours": 30,
        **invalid_payload_override,
    }
    response = await modules_client.post(
        "/api/v1/modules",
        json=payload,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "VALIDATION_ERROR"


async def test_create_learning_module_subject_and_order_conflict_rules(
    modules_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida 404 para disciplina inexistente, 422 para disciplina inativa e 409 para order_index duplicado."""
    course = _create_course_in_db(db_session_factory)
    active_subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-01",
        name="Usinagem e Tornearia",
        is_active=True,
    )
    inactive_subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="DES-OLD",
        name="Desenho Técnico Legado",
        is_active=False,
    )
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=active_subject.id,
        title="Tornearia Básica",
        order_index=1,
        practical_hours=30,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="conf"
    )

    # 1. Disciplina inexistente -> 404
    res_404 = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(uuid4()),
            "title": "Módulo Inexistente",
            "practical_hours": 20,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE

    # 2. Disciplina inativa -> 422
    res_422 = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(inactive_subject.id),
            "title": "Módulo em Disciplina Inativa",
            "practical_hours": 20,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_422.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_422.json()["message"] == LEARNING_MODULE_INACTIVE_SUBJECT_MESSAGE

    # 3. order_index duplicado na mesma disciplina -> 409
    res_409 = await modules_client.post(
        "/api/v1/modules",
        json={
            "subject_id": str(active_subject.id),
            "title": "Outro Módulo na Posição 1",
            "order_index": 1,
            "practical_hours": 25,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_409.status_code == status.HTTP_409_CONFLICT
    assert res_409.json()["message"] == LEARNING_MODULE_ORDER_CONFLICT_MESSAGE


async def test_list_subject_modules_orders_by_order_index_asc_and_supports_pagination_search(
    modules_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: GET /api/v1/subjects/{subject_id}/modules ordena por order_index ascendente."""
    course = _create_course_in_db(db_session_factory)
    subject_tornearia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-TOR-01",
        name="Tornearia Mecânica",
        workload_hours=120,
    )
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )
    subject_vazia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="SEG-TRB-01",
        name="Segurança do Trabalho",
        workload_hours=40,
    )

    # Inseridos propositalmente fora de ordem (3, 1, 4, 2)
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_tornearia.id,
        title="Torneamento Cônico e Recartilhado",
        order_index=3,
        practical_hours=30,
        description="Ajuste de carro superior em 100% de precisão.",
    )
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_tornearia.id,
        title="Segurança e Preparação do Torno",
        order_index=1,
        practical_hours=16,
        description="Fixação em placa universal e ajuste de RPM_01.",
    )
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_tornearia.id,
        title="Rosqueamento Triangular Métrico",
        order_index=4,
        practical_hours=34,
        description="Abertura de rosca M16x2.0.",
    )
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_tornearia.id,
        title="Tornearia Cilíndrica Externa",
        order_index=2,
        practical_hours=40,
        description="Faceamento e desbaste escalonado.",
    )
    # Módulo de outra disciplina não deve aparecer na listagem de Tornearia
    _create_learning_module_in_db(
        db_session_factory,
        subject_id=subject_metrologia.id,
        title="Metrologia com Paquímetro",
        order_index=1,
        practical_hours=20,
    )

    teacher_user, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ord"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="lst"
    )

    ta_table = _create_auxiliary_teacher_assignments_table(db_engine)
    with db_session_factory() as session:
        session.execute(
            ta_table.insert().values(
                id=uuid4(),
                teacher_id=teacher_user.id,
                class_id=uuid4(),
                subject_id=subject_tornearia.id,
            )
        )
        session.commit()

    # 1. Ordem ascendente rigorosa (1, 2, 3, 4) para professor alocado
    ordered_res = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert ordered_res.status_code == status.HTTP_200_OK
    ordered_body = ordered_res.json()
    assert ordered_body["total"] == 4
    assert ordered_body["page"] == 1
    assert ordered_body["limit"] == 20
    assert [item["order_index"] for item in ordered_body["data"]] == [1, 2, 3, 4]
    assert [item["title"] for item in ordered_body["data"]] == [
        "Segurança e Preparação do Torno",
        "Tornearia Cilíndrica Externa",
        "Torneamento Cônico e Recartilhado",
        "Rosqueamento Triangular Métrico",
    ]
    assert all(
        item["subject_id"] == str(subject_tornearia.id)
        for item in ordered_body["data"]
    )

    # 2. Paginação preserva ordem ascendente
    page_2_res = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules?page=2&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page_2_res.status_code == status.HTTP_200_OK
    assert [item["order_index"] for item in page_2_res.json()["data"]] == [3, 4]

    # 3. Busca textual (título e descrição, incluindo caracteres curinga escapados)
    search_title = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules?search=torne",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_title.status_code == status.HTTP_200_OK
    assert [item["order_index"] for item in search_title.json()["data"]] == [2, 3]

    search_torn_all = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules?search=torn",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_torn_all.status_code == status.HTTP_200_OK
    assert [item["order_index"] for item in search_torn_all.json()["data"]] == [1, 2, 3]

    search_percent = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules?search=100%25",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_percent.status_code == status.HTTP_200_OK
    assert [item["order_index"] for item in search_percent.json()["data"]] == [3]

    search_underscore = await modules_client.get(
        f"/api/v1/subjects/{subject_tornearia.id}/modules?search=RPM_01",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_underscore.status_code == status.HTTP_200_OK
    assert [item["order_index"] for item in search_underscore.json()["data"]] == [1]

    # 4. Disciplina válida sem módulos -> lista vazia
    empty_res = await modules_client.get(
        f"/api/v1/subjects/{subject_vazia.id}/modules",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert empty_res.status_code == status.HTTP_200_OK
    assert empty_res.json()["total"] == 0
    assert empty_res.json()["data"] == []

    # 5. Disciplina inexistente -> 404; UUID inválido -> 400
    not_found_res = await modules_client.get(
        f"/api/v1/subjects/{uuid4()}/modules",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == LEARNING_MODULE_SUBJECT_NOT_FOUND_MESSAGE

    bad_uuid_res = await modules_client.get(
        "/api/v1/subjects/invalid-uuid/modules",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert bad_uuid_res.status_code == status.HTTP_400_BAD_REQUEST
    assert bad_uuid_res.json()["error"] == "VALIDATION_ERROR"
