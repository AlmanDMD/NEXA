"""Testes unitários e de integração para Endpoints de Gestão de Competências e Habilidades Técnicas (BE-015)."""

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
from app.models import (
    Base,
    Competency,
    Course,
    LearningModule,
    ModuleCompetency,
    Subject,
    User,
)
from app.repositories.auth_repository import AuthRepository
from app.repositories.competency_repository import CompetencyRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.competency import (
    CompetencyCreateSchema,
    ModuleCompetencyCreateSchema,
    validate_competency_code_pt,
    validate_competency_title_pt,
    validate_competency_weight_pt,
    validate_required_level_pt,
)
from app.schemas.enums import CompetencyCategory, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.competency_service import (
    COMPETENCY_CODE_CONFLICT_MESSAGE,
    COMPETENCY_NOT_FOUND_MESSAGE,
    MODULE_COMPETENCY_CONFLICT_MESSAGE,
    MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE,
    MODULE_NOT_FOUND_MESSAGE,
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
def competencies_app(
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
async def competencies_client(competencies_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=competencies_app)
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


def _create_course_in_db(session_factory: sessionmaker[Session]) -> Course:
    """Helper para persistir um curso técnico SENAI diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code="TEC-MEC-01",
            name="Técnico em Mecânica Industrial",
            description="Formação técnica em usinagem e metrologia.",
            total_hours=1200,
            is_active=True,
        )


def _create_subject_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str,
    name: str,
) -> Subject:
    """Helper para persistir uma disciplina técnica diretamente via repositório."""
    with session_factory() as session:
        repo = SubjectRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            name=name,
            workload_hours=80,
            syllabus="Ementa teórico-prática SENAI.",
            is_active=True,
        )


def _create_module_in_db(
    session_factory: sessionmaker[Session],
    *,
    subject_id: UUID,
    title: str,
    order_index: int = 1,
    practical_hours: int = 40,
) -> LearningModule:
    """Helper para persistir um módulo prático diretamente via repositório."""
    with session_factory() as session:
        repo = LearningModuleRepository(session=session)
        return repo.create(
            subject_id=subject_id,
            title=title,
            order_index=order_index,
            practical_hours=practical_hours,
            description="Atividades práticas em bancada.",
            module_weight=Decimal("1.00"),
            passing_score=Decimal("6.00"),
        )


def _create_competency_in_db(
    session_factory: sessionmaker[Session],
    *,
    code: str,
    title: str,
    category: CompetencyCategory = CompetencyCategory.TECHNICAL,
    description: str | None = None,
) -> Competency:
    """Helper para persistir uma competência técnica diretamente via repositório."""
    with session_factory() as session:
        repo = CompetencyRepository(session=session)
        return repo.create(
            code=code,
            title=title,
            category=category,
            description=description,
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


def test_competency_and_module_competency_orm_and_db_constraints(
    db_session_factory: sessionmaker[Session],
) -> None:
    """Valida regras unitárias ORM e constraints SQL (uq_competencies_code, PK composta e CHECKs)."""
    course = _create_course_in_db(db_session_factory)
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
    )
    module = _create_module_in_db(
        db_session_factory,
        subject_id=subject.id,
        title="Metrologia com Paquímetro",
    )

    valid_comp = Competency(
        code="  comp-met-01  ",
        title="  Medição com Paquímetro e Tolerância H7  ",
        category=CompetencyCategory.TECHNICAL,
        description="  Leitura de escala vernier 0,02 mm.  ",
    )
    assert valid_comp.code == "COMP-MET-01"
    assert valid_comp.title == "Medição com Paquímetro e Tolerância H7"
    assert valid_comp.description == "Leitura de escala vernier 0,02 mm."

    blank_desc_comp = Competency(
        code="COMP-SEG-01",
        title="Uso de EPIs NR-12",
        category=CompetencyCategory.SAFETY,
        description="   ",
    )
    assert blank_desc_comp.description is None

    with pytest.raises(ValueError, match="entre 3 e 50 caracteres"):
        Competency(code="AB", title="Título Válido", category=CompetencyCategory.TECHNICAL)

    with pytest.raises(ValueError, match="entre 3 e 50 caracteres"):
        Competency(code="C" * 51, title="Título Válido", category=CompetencyCategory.TECHNICAL)

    with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
        Competency(code="COMP-01", title="AB", category=CompetencyCategory.TECHNICAL)

    with pytest.raises(ValueError, match="entre 1 e 5"):
        ModuleCompetency(
            module_id=module.id,
            competency_id=uuid4(),
            weight=Decimal("1.00"),
            required_level=0,
        )

    with pytest.raises(ValueError, match="entre 1 e 5"):
        ModuleCompetency(
            module_id=module.id,
            competency_id=uuid4(),
            weight=Decimal("1.00"),
            required_level=6,
        )

    with pytest.raises(ValueError, match="entre 1 e 5"):
        ModuleCompetency(
            module_id=module.id,
            competency_id=uuid4(),
            weight=Decimal("1.00"),
            required_level=True,  # type: ignore[arg-type]
        )

    for invalid_weight in (Decimal("0.00"), Decimal("-1.00"), Decimal("10.00"), True):
        with pytest.raises(ValueError, match="weight"):
            ModuleCompetency(
                module_id=module.id,
                competency_id=uuid4(),
                weight=invalid_weight,  # type: ignore[arg-type]
                required_level=3,
            )

    # Persistência válida + unicidade de code em competencies
    with db_session_factory() as session:
        session.add_all([valid_comp, blank_desc_comp])
        session.commit()

    with db_session_factory() as session:
        dup_comp = Competency(
            code="COMP-MET-01",
            title="Competência Duplicada",
            category=CompetencyCategory.PROCEDURAL,
        )
        session.add(dup_comp)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Persistência válida + PK composta impedindo duplicação em module_competencies
    with db_session_factory() as session:
        link = ModuleCompetency(
            module_id=module.id,
            competency_id=valid_comp.id,
            weight=Decimal("1.5"),
            required_level=4,
        )
        assert link.weight == Decimal("1.50")
        session.add(link)
        session.commit()

    with db_session_factory() as session:
        dup_link = ModuleCompetency(
            module_id=module.id,
            competency_id=valid_comp.id,
            weight=Decimal("1.00"),
            required_level=3,
        )
        session.add(dup_link)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # CHECK constraints SQL diretas em module_competencies
    for bad_row in (
        {"weight": 0.0, "required_level": 3},
        {"weight": 10.0, "required_level": 3},
        {"weight": 1.0, "required_level": 0},
        {"weight": 1.0, "required_level": 6},
    ):
        with db_session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    sa.text(
                        "INSERT INTO module_competencies "
                        "(module_id, competency_id, weight, required_level) "
                        "VALUES (:module_id, :competency_id, :weight, :required_level)"
                    ),
                    {
                        "module_id": str(module.id).replace("-", ""),
                        "competency_id": str(blank_desc_comp.id).replace("-", ""),
                        **bad_row,
                    },
                )
                session.commit()
            session.rollback()


def test_pydantic_validators_for_competencies_and_module_links() -> None:
    """Valida regras Pydantic de código, título, peso e nível requerido (1 a 5)."""
    assert validate_competency_code_pt("  comp-tor-01 ") == "COMP-TOR-01"
    assert validate_competency_title_pt("  Operação   Segura   NR-12  ") == "Operação Segura NR-12"
    assert validate_competency_weight_pt("2.5") == Decimal("2.50")
    assert validate_competency_weight_pt(1) == Decimal("1.00")
    assert validate_required_level_pt(1) == 1
    assert validate_required_level_pt("5") == 5

    for invalid_code in ("AB", "X" * 51, "COMP 01", "<script>"):
        with pytest.raises(Exception):
            validate_competency_code_pt(invalid_code)

    for invalid_title in ("AB", "Y" * 151, "<b>Segurança</b>"):
        with pytest.raises(Exception):
            validate_competency_title_pt(invalid_title)

    for invalid_weight in (0, 0.00, -1, 10.00, 1.234, True, False, "abc", float("nan"), float("inf")):
        with pytest.raises(Exception):
            validate_competency_weight_pt(invalid_weight)

    for invalid_level in (0, -1, 6, 10, True, False, 2.5, "0", "6", "alto"):
        with pytest.raises(Exception):
            validate_required_level_pt(invalid_level)

    comp_schema = CompetencyCreateSchema(
        code="  comp-pro-01 ",
        title="  Sequenciamento   de   Usinagem ",
        category=CompetencyCategory.PROCEDURAL,
        description="  Ordem de serviço e seleção de ferramentas.  ",
    )
    assert comp_schema.code == "COMP-PRO-01"
    assert comp_schema.title == "Sequenciamento de Usinagem"
    assert comp_schema.category == CompetencyCategory.PROCEDURAL

    link_schema = ModuleCompetencyCreateSchema(competency_id=uuid4())
    assert link_schema.weight == Decimal("1.00")
    assert link_schema.required_level == 3


async def test_competencies_rbac_and_contextual_teacher_access(
    competencies_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante RBAC (401/403) e alocação docente contextual ao vincular e consultar competências de módulos."""
    course = _create_course_in_db(db_session_factory)
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-01",
        name="Metrologia Dimensional",
    )
    subject_tornearia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-01",
        name="Tornearia Mecânica",
    )
    module_metrologia = _create_module_in_db(
        db_session_factory,
        subject_id=subject_metrologia.id,
        title="Metrologia com Micrômetro",
    )
    module_tornearia = _create_module_in_db(
        db_session_factory,
        subject_id=subject_tornearia.id,
        title="Tornearia Cilíndrica",
    )
    competency = _create_competency_in_db(
        db_session_factory,
        code="COMP-MET-01",
        title="Medição com Micrômetro Centesimal",
        category=CompetencyCategory.TECHNICAL,
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

    comp_payload = {
        "code": "COMP-SEG-01",
        "title": "Operação Segura NR-12",
        "category": "SAFETY",
    }
    link_payload = {
        "competency_id": str(competency.id),
        "weight": "1.50",
        "required_level": 4,
    }

    # 1. Sem token -> 401; STUDENT -> 403 em todas as 4 rotas
    all_routes: list[tuple[str, str, dict[str, Any] | None]] = [
        ("GET", "/api/v1/competencies", None),
        ("POST", "/api/v1/competencies", comp_payload),
        ("POST", f"/api/v1/modules/{module_metrologia.id}/competencies", link_payload),
        ("GET", f"/api/v1/modules/{module_metrologia.id}/competencies", None),
    ]
    for method, url, body in all_routes:
        unauth_res = await competencies_client.request(method, url, json=body)
        assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

        student_res = await competencies_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_res.status_code == status.HTTP_403_FORBIDDEN
        assert student_res.json()["message"] == "Acesso não autorizado para seu perfil"

    # 2. TEACHER pode listar catálogo (200), mas não pode criar no catálogo global (403)
    tch_list = await competencies_client.get(
        "/api/v1/competencies",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert tch_list.status_code == status.HTTP_200_OK

    tch_create_comp = await competencies_client.post(
        "/api/v1/competencies",
        json=comp_payload,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert tch_create_comp.status_code == status.HTTP_403_FORBIDDEN

    # 3. TEACHER sem tabela teacher_assignments -> 403 nos endpoints de módulo
    for method, url, body in (
        ("POST", f"/api/v1/modules/{module_metrologia.id}/competencies", link_payload),
        ("GET", f"/api/v1/modules/{module_metrologia.id}/competencies", None),
    ):
        tch_no_table = await competencies_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert tch_no_table.status_code == status.HTTP_403_FORBIDDEN
        assert tch_no_table.json()["message"] == MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE

    # 4. Cria teacher_assignments alocando docente apenas em Metrologia
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

    tch_link_ok = await competencies_client.post(
        f"/api/v1/modules/{module_metrologia.id}/competencies",
        json=link_payload,
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert tch_link_ok.status_code == status.HTTP_201_CREATED

    tch_get_ok = await competencies_client.get(
        f"/api/v1/modules/{module_metrologia.id}/competencies",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert tch_get_ok.status_code == status.HTTP_200_OK
    assert tch_get_ok.json()["total_competencies"] == 1

    # Módulo de Tornearia (não alocado) -> 403
    for method, url, body in (
        ("POST", f"/api/v1/modules/{module_tornearia.id}/competencies", link_payload),
        ("GET", f"/api/v1/modules/{module_tornearia.id}/competencies", None),
    ):
        tch_denied = await competencies_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert tch_denied.status_code == status.HTTP_403_FORBIDDEN
        assert tch_denied.json()["message"] == MODULE_COMPETENCY_TEACHER_FORBIDDEN_MESSAGE

    # 5. COORDINATOR e ADMIN acessam todas as rotas sem alocação
    coord_comp = await competencies_client.post(
        "/api/v1/competencies",
        json=comp_payload,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert coord_comp.status_code == status.HTTP_201_CREATED

    admin_link = await competencies_client.post(
        f"/api/v1/modules/{module_tornearia.id}/competencies",
        json={"competency_id": coord_comp.json()["id"], "weight": "2.00", "required_level": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_link.status_code == status.HTTP_201_CREATED


async def test_create_competency_unique_code_and_validations(
    competencies_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: POST /api/v1/competencies valida código único (409) e payload Pydantic (400)."""
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="c1"
    )

    payloads = [
        {
            "code": "  comp-met-01  ",
            "title": "  Medição   com   Paquímetro e Tolerância H7  ",
            "category": "TECHNICAL",
            "description": "  Leitura em escala 0,02 mm e verificação dimensional.  ",
        },
        {
            "code": "COMP-SEG-01",
            "title": "Operação Segura em Torno NR-12",
            "category": "SAFETY",
            "description": None,
        },
        {
            "code": "COMP-PRO-01",
            "title": "Preparação e Sequenciamento de Usinagem",
            "category": "PROCEDURAL",
        },
    ]

    for item in payloads:
        res = await competencies_client.post(
            "/api/v1/competencies",
            json=item,
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res.status_code == status.HTTP_201_CREATED

    with db_session_factory() as session:
        persisted = session.scalar(select(Competency).where(Competency.code == "COMP-MET-01"))
        assert persisted is not None
        assert persisted.title == "Medição com Paquímetro e Tolerância H7"
        assert persisted.category == CompetencyCategory.TECHNICAL

    # Código duplicado (exato e case-insensitive com espaços) -> HTTP 409
    for dup_code in ("COMP-MET-01", "  comp-met-01  "):
        dup_res = await competencies_client.post(
            "/api/v1/competencies",
            json={
                "code": dup_code,
                "title": "Competência Repetida",
                "category": "TECHNICAL",
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert dup_res.status_code == status.HTTP_409_CONFLICT
        assert dup_res.json()["message"] == COMPETENCY_CODE_CONFLICT_MESSAGE

    # Payloads inválidos -> HTTP 400
    invalid_payloads: list[dict[str, Any]] = [
        {"code": "AB", "title": "Título Válido", "category": "TECHNICAL"},
        {"code": "COMP 01", "title": "Título Válido", "category": "TECHNICAL"},
        {"code": "COMP-99", "title": "AB", "category": "TECHNICAL"},
        {"code": "COMP-99", "title": "<script>alert(1)</script>", "category": "TECHNICAL"},
        {"code": "COMP-99", "title": "Título Válido", "category": "INVALID_CAT"},
        {"code": "COMP-99", "title": "Título Válido", "category": "TECHNICAL", "extra": 123},
    ]
    for bad in invalid_payloads:
        bad_res = await competencies_client.post(
            "/api/v1/competencies",
            json=bad,
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert bad_res.status_code == status.HTTP_400_BAD_REQUEST
        assert bad_res.json()["error"] == "VALIDATION_ERROR"


async def test_list_competencies_supports_category_filter_search_and_pagination(
    competencies_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/competencies com paginação, filtro por categoria e busca textual."""
    _create_competency_in_db(
        db_session_factory,
        code="COMP-TOR-01",
        title="Torneamento Cilíndrico Externo",
        category=CompetencyCategory.TECHNICAL,
        description="Ajuste de avanço e tolerância H7 em 100% das peças.",
    )
    _create_competency_in_db(
        db_session_factory,
        code="COMP-MET-01",
        title="Medição com Micrômetro Centesimal",
        category=CompetencyCategory.TECHNICAL,
        description="Controle dimensional ISO_2768.",
    )
    _create_competency_in_db(
        db_session_factory,
        code="COMP-SEG-01",
        title="Segurança em Máquinas NR-12",
        category=CompetencyCategory.SAFETY,
        description="Uso obrigatório de óculos e proteção de placa.",
    )
    _create_competency_in_db(
        db_session_factory,
        code="COMP-PRO-01",
        title="Leitura de Ordem de Serviço Técnica",
        category=CompetencyCategory.PROCEDURAL,
        description="Organização da bancada e calibração prévia.",
    )

    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="lst"
    )

    # 1. Paginação ordenada por code ASC
    page_1 = await competencies_client.get(
        "/api/v1/competencies?page=1&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert page_1.status_code == status.HTTP_200_OK
    b1 = page_1.json()
    assert b1["total"] == 4
    assert [item["code"] for item in b1["data"]] == ["COMP-MET-01", "COMP-PRO-01"]

    page_2 = await competencies_client.get(
        "/api/v1/competencies?page=2&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert page_2.status_code == status.HTTP_200_OK
    assert [item["code"] for item in page_2.json()["data"]] == ["COMP-SEG-01", "COMP-TOR-01"]

    # 2. Filtro por categoria
    tech_res = await competencies_client.get(
        "/api/v1/competencies?category=TECHNICAL",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert tech_res.status_code == status.HTTP_200_OK
    assert tech_res.json()["total"] == 2
    assert [item["code"] for item in tech_res.json()["data"]] == ["COMP-MET-01", "COMP-TOR-01"]

    safety_res = await competencies_client.get(
        "/api/v1/competencies?category=SAFETY",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert safety_res.status_code == status.HTTP_200_OK
    assert safety_res.json()["total"] == 1
    assert safety_res.json()["data"][0]["code"] == "COMP-SEG-01"

    # 3. Busca textual (título, código e descrição com % e _ escapados)
    search_desc = await competencies_client.get(
        "/api/v1/competencies?search=bancada",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_desc.status_code == status.HTTP_200_OK
    assert [item["code"] for item in search_desc.json()["data"]] == ["COMP-PRO-01"]

    search_percent = await competencies_client.get(
        "/api/v1/competencies?search=100%25",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_percent.status_code == status.HTTP_200_OK
    assert [item["code"] for item in search_percent.json()["data"]] == ["COMP-TOR-01"]

    search_underscore = await competencies_client.get(
        "/api/v1/competencies?search=ISO_2768",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_underscore.status_code == status.HTTP_200_OK
    assert [item["code"] for item in search_underscore.json()["data"]] == ["COMP-MET-01"]

    # 4. Combinação category + search e categoria inválida -> 400
    combo_res = await competencies_client.get(
        "/api/v1/competencies?category=TECHNICAL&search=micrômetro",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert combo_res.status_code == status.HTTP_200_OK
    assert [item["code"] for item in combo_res.json()["data"]] == ["COMP-MET-01"]

    bad_cat_res = await competencies_client.get(
        "/api/v1/competencies?category=OUTRA",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert bad_cat_res.status_code == status.HTTP_400_BAD_REQUEST


async def test_link_competency_to_module_required_level_weight_and_conflicts(
    competencies_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Vinculação com peso e nível requerido entre 1 e 5, conflitos e 404."""
    course = _create_course_in_db(db_session_factory)
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="USN-01",
        name="Usinagem e Tornearia",
    )
    module_1 = _create_module_in_db(
        db_session_factory,
        subject_id=subject.id,
        title="Tornearia Cilíndrica",
        order_index=1,
    )
    module_2 = _create_module_in_db(
        db_session_factory,
        subject_id=subject.id,
        title="Tornearia Cônica",
        order_index=2,
    )

    comp_tech = _create_competency_in_db(
        db_session_factory,
        code="COMP-TOR-01",
        title="Desbaste e Acabamento em Torno",
        category=CompetencyCategory.TECHNICAL,
    )
    comp_safety = _create_competency_in_db(
        db_session_factory,
        code="COMP-SEG-01",
        title="Uso de EPIs NR-12",
        category=CompetencyCategory.SAFETY,
    )
    comp_proc = _create_competency_in_db(
        db_session_factory,
        code="COMP-PRO-01",
        title="Inspeção Dimensional Pós-Usinagem",
        category=CompetencyCategory.PROCEDURAL,
    )

    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="lnk"
    )

    # 1. Limite inferior required_level=1 e peso padrão/explícito
    res_lvl_1 = await competencies_client.post(
        f"/api/v1/modules/{module_1.id}/competencies",
        json={
            "competency_id": str(comp_proc.id),
            "required_level": 1,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_lvl_1.status_code == status.HTTP_201_CREATED
    b1 = res_lvl_1.json()
    assert b1["module_id"] == str(module_1.id)
    assert b1["competency_id"] == str(comp_proc.id)
    assert b1["weight"] == "1.00"
    assert b1["required_level"] == 1
    assert b1["competency"]["code"] == "COMP-PRO-01"

    # 2. Limite superior required_level=5 com peso customizado
    res_lvl_5 = await competencies_client.post(
        f"/api/v1/modules/{module_1.id}/competencies",
        json={
            "competency_id": str(comp_tech.id),
            "weight": "2.50",
            "required_level": 5,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_lvl_5.status_code == status.HTTP_201_CREATED
    assert res_lvl_5.json()["weight"] == "2.50"
    assert res_lvl_5.json()["required_level"] == 5

    # 3. Reuso da mesma competência transversal em outro módulo é permitido
    for target_mod in (module_1, module_2):
        res_reuse = await competencies_client.post(
            f"/api/v1/modules/{target_mod.id}/competencies",
            json={"competency_id": str(comp_safety.id)},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res_reuse.status_code == status.HTTP_201_CREATED
        assert res_reuse.json()["required_level"] == 3
        assert res_reuse.json()["weight"] == "1.00"

    # 4. Vínculo duplicado no mesmo módulo -> HTTP 409
    dup_link_res = await competencies_client.post(
        f"/api/v1/modules/{module_1.id}/competencies",
        json={
            "competency_id": str(comp_tech.id),
            "weight": "1.00",
            "required_level": 4,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert dup_link_res.status_code == status.HTTP_409_CONFLICT
    assert dup_link_res.json()["message"] == MODULE_COMPETENCY_CONFLICT_MESSAGE

    # 5. required_level fora do intervalo 1..5 ou inválido -> HTTP 400
    for bad_level in (0, -1, 6, 10, True, False, 3.5, "0", "6", "alto"):
        bad_lvl_res = await competencies_client.post(
            f"/api/v1/modules/{module_2.id}/competencies",
            json={
                "competency_id": str(comp_tech.id),
                "weight": "1.00",
                "required_level": bad_level,
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert bad_lvl_res.status_code == status.HTTP_400_BAD_REQUEST
        assert bad_lvl_res.json()["error"] == "VALIDATION_ERROR"
        assert any(d["field"] == "required_level" for d in bad_lvl_res.json()["details"])

    # 6. weight inválido -> HTTP 400
    for bad_weight in (0, "0.00", -1, 10.00, 1.234, True):
        bad_w_res = await competencies_client.post(
            f"/api/v1/modules/{module_2.id}/competencies",
            json={
                "competency_id": str(comp_tech.id),
                "weight": bad_weight,
                "required_level": 3,
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert bad_w_res.status_code == status.HTTP_400_BAD_REQUEST
        assert bad_w_res.json()["error"] == "VALIDATION_ERROR"

    # 7. Módulo inexistente (404), competência inexistente (404) e UUID inválido (400)
    mod_404 = await competencies_client.post(
        f"/api/v1/modules/{uuid4()}/competencies",
        json={"competency_id": str(comp_tech.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert mod_404.status_code == status.HTTP_404_NOT_FOUND
    assert mod_404.json()["message"] == MODULE_NOT_FOUND_MESSAGE

    comp_404 = await competencies_client.post(
        f"/api/v1/modules/{module_2.id}/competencies",
        json={"competency_id": str(uuid4())},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert comp_404.status_code == status.HTTP_404_NOT_FOUND
    assert comp_404.json()["message"] == COMPETENCY_NOT_FOUND_MESSAGE

    bad_uuid = await competencies_client.post(
        "/api/v1/modules/invalid-uuid/competencies",
        json={"competency_id": str(comp_tech.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert bad_uuid.status_code == status.HTTP_400_BAD_REQUEST


async def test_consult_aggregated_competencies_by_module_for_radar_chart(
    competencies_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Consulta agregada por módulo (endpoint dedicado + GET /subjects/{id}/modules)."""
    course = _create_course_in_db(db_session_factory)
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-01",
        name="Metrologia e Usinagem",
    )
    module_with_comps = _create_module_in_db(
        db_session_factory,
        subject_id=subject.id,
        title="Metrologia com Micrômetro e Paquímetro",
        order_index=1,
        practical_hours=32,
    )
    module_empty = _create_module_in_db(
        db_session_factory,
        subject_id=subject.id,
        title="Módulo Introdutório Sem Competências",
        order_index=2,
        practical_hours=8,
    )

    comp_tech_1 = _create_competency_in_db(
        db_session_factory,
        code="COMP-MET-01",
        title="Medição com Paquímetro e Tolerância H7",
        category=CompetencyCategory.TECHNICAL,
    )
    comp_tech_2 = _create_competency_in_db(
        db_session_factory,
        code="COMP-MET-02",
        title="Leitura de Micrômetro Centesimal",
        category=CompetencyCategory.TECHNICAL,
    )
    comp_safety = _create_competency_in_db(
        db_session_factory,
        code="COMP-SEG-01",
        title="Segurança e EPIs em Oficina",
        category=CompetencyCategory.SAFETY,
    )
    comp_proc = _create_competency_in_db(
        db_session_factory,
        code="COMP-PRO-01",
        title="Registro de Relatório de Controle Dimensional",
        category=CompetencyCategory.PROCEDURAL,
    )

    with db_session_factory() as session:
        repo = CompetencyRepository(session=session)
        repo.link_to_module(
            module_id=module_with_comps.id,
            competency_id=comp_safety.id,
            weight=Decimal("1.00"),
            required_level=3,
        )
        repo.link_to_module(
            module_id=module_with_comps.id,
            competency_id=comp_tech_2.id,
            weight=Decimal("2.50"),
            required_level=5,
        )
        repo.link_to_module(
            module_id=module_with_comps.id,
            competency_id=comp_proc.id,
            weight=Decimal("1.25"),
            required_level=2,
        )
        repo.link_to_module(
            module_id=module_with_comps.id,
            competency_id=comp_tech_1.id,
            weight=Decimal("1.75"),
            required_level=4,
        )

    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="agg"
    )

    # 1. Endpoint dedicado GET /api/v1/modules/{module_id}/competencies
    agg_res = await competencies_client.get(
        f"/api/v1/modules/{module_with_comps.id}/competencies",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert agg_res.status_code == status.HTTP_200_OK
    agg_body = agg_res.json()
    assert agg_body["module"] == {
        "id": str(module_with_comps.id),
        "subject_id": str(subject.id),
        "title": "Metrologia com Micrômetro e Paquímetro",
        "order_index": 1,
        "practical_hours": 32,
        "passing_score": "6.00",
    }
    assert agg_body["total_competencies"] == 4
    assert agg_body["total_weight"] == "6.50"
    assert agg_body["categories_summary"] == {
        "TECHNICAL": 2,
        "SAFETY": 1,
        "PROCEDURAL": 1,
    }
    assert [item["competency"]["code"] for item in agg_body["data"]] == [
        "COMP-MET-01",
        "COMP-MET-02",
        "COMP-PRO-01",
        "COMP-SEG-01",
    ]
    assert agg_body["data"][0]["weight"] == "1.75"
    assert agg_body["data"][0]["required_level"] == 4

    # 2. Módulo sem competências vinculadas
    empty_res = await competencies_client.get(
        f"/api/v1/modules/{module_empty.id}/competencies",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert empty_res.status_code == status.HTTP_200_OK
    empty_body = empty_res.json()
    assert empty_body["total_competencies"] == 0
    assert empty_body["total_weight"] == "0.00"
    assert empty_body["categories_summary"] == {
        "TECHNICAL": 0,
        "SAFETY": 0,
        "PROCEDURAL": 0,
    }
    assert empty_body["data"] == []

    # 3. Consulta de módulos da disciplina (BE-014) também entrega competências agregadas por módulo
    modules_res = await competencies_client.get(
        f"/api/v1/subjects/{subject.id}/modules",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert modules_res.status_code == status.HTTP_200_OK
    modules_data = modules_res.json()["data"]
    assert len(modules_data) == 2
    assert len(modules_data[0]["competencies"]) == 4
    assert {c["competency"]["code"] for c in modules_data[0]["competencies"]} == {
        "COMP-MET-01",
        "COMP-MET-02",
        "COMP-PRO-01",
        "COMP-SEG-01",
    }
    assert modules_data[1]["competencies"] == []

    # 4. Módulo inexistente (404) e UUID inválido (400)
    res_404 = await competencies_client.get(
        f"/api/v1/modules/{uuid4()}/competencies",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == MODULE_NOT_FOUND_MESSAGE

    res_400 = await competencies_client.get(
        "/api/v1/modules/bad-uuid/competencies",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_400.status_code == status.HTTP_400_BAD_REQUEST
