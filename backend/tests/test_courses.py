"""Testes unitários e de integração para Endpoints CRUD de Cursos Técnicos SENAI (BE-011)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import AcademicClass, Base, Course, User
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.enums import ClassStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.course_service import (
    COURSE_CODE_CONFLICT_MESSAGE,
    COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE,
    COURSE_NOT_FOUND_MESSAGE,
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
def courses_app(
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
async def courses_client(courses_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=courses_app)
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
    code: str,
    name: str,
    description: str | None = None,
    total_hours: int = 1200,
    is_active: bool = True,
) -> Course:
    """Helper para persistir um curso diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description=description,
            total_hours=total_hours,
            is_active=is_active,
        )


def test_course_orm_model_validations() -> None:
    """Valida restrições unitárias de código, nome e carga horária no modelo ORM Course."""
    course = Course(
        code="  tec-mec-01 ",
        name="  Técnico em Mecânica  ",
        description="Formação em usinagem e manutenção.",
        total_hours=1200,
    )
    assert course.code == "TEC-MEC-01"
    assert course.name == "Técnico em Mecânica"
    assert course.total_hours == 1200

    with pytest.raises(ValueError, match="entre 3 e 30 caracteres"):
        Course(code="AB", name="Curso Válido", total_hours=800)

    with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
        Course(code="TEC-01", name="AB", total_hours=800)

    with pytest.raises(ValueError, match="maior que zero"):
        Course(code="TEC-01", name="Curso Válido", total_hours=0)

    with pytest.raises(ValueError, match="maior que zero"):
        Course(code="TEC-01", name="Curso Válido", total_hours=-100)

    with pytest.raises(ValueError, match="maior que zero"):
        Course(code="TEC-01", name="Curso Válido", total_hours=True)  # type: ignore[arg-type]


async def test_courses_rbac_blocks_unauthenticated_student_and_teacher(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante restrição RBAC (401 sem token e 403 para STUDENT/TEACHER) em todas as rotas."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="001"
    )
    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="002"
    )

    payload = {
        "code": "TEC-ADS-01",
        "name": "Técnico em Desenvolvimento de Sistemas",
        "total_hours": 1200,
    }
    endpoints: list[tuple[str, str, dict[str, Any] | None]] = [
        ("GET", "/api/v1/courses", None),
        ("POST", "/api/v1/courses", payload),
        ("GET", f"/api/v1/courses/{course.id}", None),
        ("PUT", f"/api/v1/courses/{course.id}", {"name": "Nome Atualizado"}),
        ("DELETE", f"/api/v1/courses/{course.id}", None),
    ]

    for method, url, body in endpoints:
        unauth_res = await courses_client.request(method, url, json=body)
        assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

        for forbidden_token in (student_token, teacher_token):
            forbidden_res = await courses_client.request(
                method,
                url,
                json=body,
                headers={"Authorization": f"Bearer {forbidden_token}"},
            )
            assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN
            err_body = forbidden_res.json()
            assert err_body["error"] == "FORBIDDEN"
            assert err_body["message"] == "Acesso não autorizado para seu perfil"


async def test_courses_rbac_allows_admin_and_coordinator(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que ADMIN e COORDINATOR têm acesso completo ao CRUD de cursos."""
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="adm"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd"
    )

    create_res = await courses_client.post(
        "/api/v1/courses",
        json={
            "code": "TEC-ELT-01",
            "name": "Técnico em Eletromecânica",
            "total_hours": 1400,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_res.status_code == status.HTTP_201_CREATED
    course_id = create_res.json()["id"]

    list_res = await courses_client.get(
        "/api/v1/courses",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1

    get_res = await courses_client.get(
        f"/api/v1/courses/{course_id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert get_res.status_code == status.HTTP_200_OK

    put_res = await courses_client.put(
        f"/api/v1/courses/{course_id}",
        json={"total_hours": 1500},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert put_res.status_code == status.HTTP_200_OK
    assert put_res.json()["total_hours"] == 1500

    del_res = await courses_client.delete(
        f"/api/v1/courses/{course_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["is_active"] is False


async def test_create_course_success_normalizes_fields_and_persists(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida POST /api/v1/courses com normalização de código/nome e persistência no banco."""
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="c1"
    )

    response = await courses_client.post(
        "/api/v1/courses",
        json={
            "code": "  tec-mec-01  ",
            "name": "  Técnico   em   Mecânica  ",
            "description": "  Curso técnico de manufatura e usinagem CNC.  ",
            "total_hours": 1200,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    UUID(body["id"])
    assert body["code"] == "TEC-MEC-01"
    assert body["name"] == "Técnico em Mecânica"
    assert body["description"] == "Curso técnico de manufatura e usinagem CNC."
    assert body["total_hours"] == 1200
    assert body["is_active"] is True
    assert "created_at" in body
    assert "updated_at" in body

    with db_session_factory() as session:
        persisted = session.scalar(select(Course).where(Course.code == "TEC-MEC-01"))
        assert persisted is not None
        assert persisted.name == "Técnico em Mecânica"
        assert persisted.total_hours == 1200


async def test_create_course_rejects_duplicate_code_with_409(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: POST rejeita código duplicado (exato ou case-insensitive) com HTTP 409."""
    _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="dup"
    )

    for duplicate_code in ("TEC-MEC-01", "  tec-mec-01  "):
        response = await courses_client.post(
            "/api/v1/courses",
            json={
                "code": duplicate_code,
                "name": "Outro Nome de Curso",
                "total_hours": 1000,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.json()
        assert body["error"] == "CONFLICT"
        assert body["message"] == COURSE_CODE_CONFLICT_MESSAGE


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"code": "AB", "name": "Técnico em Mecânica", "total_hours": 1200},
        {"code": "TEC 01", "name": "Técnico em Mecânica", "total_hours": 1200},
        {"code": "TEC-01", "name": "AB", "total_hours": 1200},
        {"code": "TEC-01", "name": "Técnico <script>alert(1)</script>", "total_hours": 1200},
        {"code": "TEC-01", "name": "Técnico em Mecânica", "description": "<iframe src=x>", "total_hours": 1200},
        {"code": "TEC-01", "name": "Técnico em Mecânica", "total_hours": 0},
        {"code": "TEC-01", "name": "Técnico em Mecânica", "total_hours": -400},
        {"code": "TEC-01", "name": "Técnico em Mecânica", "total_hours": True},
        {"code": "TEC-01", "name": "Técnico em Mecânica", "total_hours": 1200, "extra_field": "x"},
    ],
)
async def test_create_course_rejects_invalid_pydantic_payloads(
    invalid_payload: dict[str, Any],
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida que entradas inválidas de código, nome, XSS, carga horária e campos extras retornam 400."""
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="val"
    )

    response = await courses_client.post(
        "/api/v1/courses",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "VALIDATION_ERROR"


async def test_list_courses_pagination_search_and_status_filter(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: GET /api/v1/courses retorna { data, total, page, limit } com paginação e busca."""
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="lst"
    )

    _create_course_in_db(
        db_session_factory,
        code="TEC-ADS-01",
        name="Análise e Desenvolvimento de Sistemas",
        description="Programação, APIs e Banco de Dados 100% prático",
        total_hours=1200,
        is_active=True,
    )
    _create_course_in_db(
        db_session_factory,
        code="TEC-AUT-01",
        name="Automação Industrial",
        description="CLPs, robótica e controle",
        total_hours=1400,
        is_active=True,
    )
    _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Mecânica de Precisão",
        description="Tornearia CNC e metrologia",
        total_hours=1200,
        is_active=True,
    )
    _create_course_in_db(
        db_session_factory,
        code="TEC-LOG-01",
        name="Logística Integrada",
        description="Cadeia de suprimentos (inativo)",
        total_hours=800,
        is_active=False,
    )

    # 1. Paginação e contrato exato { data, total, page, limit }
    page1_res = await courses_client.get(
        "/api/v1/courses?page=1&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page1_res.status_code == status.HTTP_200_OK
    page1_body = page1_res.json()
    assert set(page1_body.keys()) == {"data", "total", "page", "limit"}
    assert page1_body["total"] == 4
    assert page1_body["page"] == 1
    assert page1_body["limit"] == 2
    assert len(page1_body["data"]) == 2
    assert [item["code"] for item in page1_body["data"]] == ["TEC-ADS-01", "TEC-AUT-01"]

    page2_res = await courses_client.get(
        "/api/v1/courses?page=2&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page2_res.status_code == status.HTTP_200_OK
    page2_body = page2_res.json()
    assert page2_body["total"] == 4
    assert page2_body["page"] == 2
    assert [item["code"] for item in page2_body["data"]] == ["TEC-LOG-01", "TEC-MEC-01"]

    # Página além do total mantém total e retorna data vazio
    page3_res = await courses_client.get(
        "/api/v1/courses?page=3&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page3_res.status_code == status.HTTP_200_OK
    assert page3_res.json() == {"data": [], "total": 4, "page": 3, "limit": 2}

    # 2. Busca case-insensitive por código, nome e descrição (incluindo curinga '%' escapado)
    search_name = await courses_client.get(
        "/api/v1/courses?search=tornearia",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_name.status_code == status.HTTP_200_OK
    assert [item["code"] for item in search_name.json()["data"]] == ["TEC-MEC-01"]

    search_code = await courses_client.get(
        "/api/v1/courses?search=tec-aut",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_code.status_code == status.HTTP_200_OK
    assert [item["code"] for item in search_code.json()["data"]] == ["TEC-AUT-01"]

    search_wildcard = await courses_client.get(
        "/api/v1/courses",
        params={"search": "100%"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_wildcard.status_code == status.HTTP_200_OK
    assert search_wildcard.json()["total"] == 1
    assert search_wildcard.json()["data"][0]["code"] == "TEC-ADS-01"

    # 3. Filtro por is_active
    active_res = await courses_client.get(
        "/api/v1/courses?is_active=true",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert active_res.status_code == status.HTTP_200_OK
    assert active_res.json()["total"] == 3

    inactive_res = await courses_client.get(
        "/api/v1/courses?is_active=false",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert inactive_res.status_code == status.HTTP_200_OK
    assert inactive_res.json()["total"] == 1
    assert inactive_res.json()["data"][0]["code"] == "TEC-LOG-01"

    # 4. Query params inválidos retornam HTTP 400
    invalid_query_res = await courses_client.get(
        "/api/v1/courses?page=0&limit=101",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert invalid_query_res.status_code == status.HTTP_400_BAD_REQUEST


async def test_get_course_by_id_success_and_errors(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/courses/{id} para sucesso (200), inexistente (404) e UUID inválido (400)."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        description="Descrição completa.",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="get"
    )

    ok_res = await courses_client.get(
        f"/api/v1/courses/{course.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert ok_res.status_code == status.HTTP_200_OK
    assert ok_res.json()["id"] == str(course.id)
    assert ok_res.json()["code"] == "TEC-MEC-01"

    not_found_res = await courses_client.get(
        f"/api/v1/courses/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == COURSE_NOT_FOUND_MESSAGE

    bad_uuid_res = await courses_client.get(
        "/api/v1/courses/nao-eh-uuid",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert bad_uuid_res.status_code == status.HTTP_400_BAD_REQUEST


async def test_update_course_partial_full_and_conflict_validation(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida PUT /api/v1/courses/{id} com atualização parcial, conflito de código, limpeza de descrição e 404/400."""
    course_1 = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        description="Descrição inicial.",
        total_hours=1200,
    )
    _create_course_in_db(
        db_session_factory,
        code="TEC-ADS-01",
        name="Técnico em ADS",
        total_hours=1200,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="upd"
    )

    # Atualização mantendo o próprio código e limpando descrição com null
    ok_res = await courses_client.put(
        f"/api/v1/courses/{course_1.id}",
        json={
            "code": "tec-mec-01",
            "name": "Técnico em Mecânica Industrial",
            "description": None,
            "total_hours": 1440,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert ok_res.status_code == status.HTTP_200_OK
    body = ok_res.json()
    assert body["code"] == "TEC-MEC-01"
    assert body["name"] == "Técnico em Mecânica Industrial"
    assert body["description"] is None
    assert body["total_hours"] == 1440

    # Conflito ao tentar usar código de outro curso existente
    conflict_res = await courses_client.put(
        f"/api/v1/courses/{course_1.id}",
        json={"code": "TEC-ADS-01"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert conflict_res.status_code == status.HTTP_409_CONFLICT
    assert conflict_res.json()["message"] == COURSE_CODE_CONFLICT_MESSAGE

    # Payload vazio ou nulo em campo obrigatório
    empty_res = await courses_client.put(
        f"/api/v1/courses/{course_1.id}",
        json={},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert empty_res.status_code == status.HTTP_400_BAD_REQUEST

    null_code_res = await courses_client.put(
        f"/api/v1/courses/{course_1.id}",
        json={"code": None},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert null_code_res.status_code == status.HTTP_400_BAD_REQUEST

    # Curso inexistente
    not_found_res = await courses_client.put(
        f"/api/v1/courses/{uuid4()}",
        json={"name": "Novo Nome"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND


async def test_soft_delete_course_sets_is_active_false_and_preserves_record(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Exclusão lógica via DELETE (is_active=False) mantendo o registro no banco."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="del"
    )

    del_res = await courses_client.delete(
        f"/api/v1/courses/{course.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == status.HTTP_200_OK
    assert del_res.json()["is_active"] is False

    # Idempotência ao desativar curso já inativo
    del_again = await courses_client.delete(
        f"/api/v1/courses/{course.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_again.status_code == status.HTTP_200_OK
    assert del_again.json()["is_active"] is False

    # Registro preservado fisicamente no banco com is_active=False
    with db_session_factory() as session:
        persisted = session.scalar(select(Course).where(Course.id == course.id))
        assert persisted is not None
        assert persisted.is_active is False

    # Curso inexistente retorna 404
    not_found_res = await courses_client.delete(
        f"/api/v1/courses/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND


async def test_deactivate_course_blocked_when_active_classes_exist(
    courses_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Observação Técnica: Impedir desativação (DELETE e PUT is_active=False) se houver turmas ACTIVE vinculadas."""
    course_with_active = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    course_with_inactive_classes = _create_course_in_db(
        db_session_factory,
        code="TEC-ELT-01",
        name="Técnico em Eletromecânica",
    )

    with db_session_factory() as session:
        session.add_all(
            [
                AcademicClass(
                    course_id=course_with_active.id,
                    code="MEC-2026-1T",
                    period="2026.1",
                    shift=Shift.MORNING,
                    max_students=40,
                    status=ClassStatus.ACTIVE,
                    start_date=date(2026, 2, 2),
                    end_date=date(2026, 6, 30),
                ),
                AcademicClass(
                    course_id=course_with_inactive_classes.id,
                    code="ELT-2025-2T",
                    period="2025.2",
                    shift=Shift.AFTERNOON,
                    max_students=35,
                    status=ClassStatus.COMPLETED,
                    start_date=date(2025, 8, 1),
                    end_date=date(2025, 12, 15),
                ),
                AcademicClass(
                    course_id=course_with_inactive_classes.id,
                    code="ELT-2026-2T",
                    period="2026.2",
                    shift=Shift.NIGHT,
                    max_students=35,
                    status=ClassStatus.PLANNING,
                    start_date=date(2026, 8, 3),
                    end_date=date(2026, 12, 18),
                ),
                AcademicClass(
                    course_id=course_with_inactive_classes.id,
                    code="ELT-2024-1T",
                    period="2024.1",
                    shift=Shift.MORNING,
                    max_students=30,
                    status=ClassStatus.ARCHIVED,
                    start_date=date(2024, 2, 5),
                    end_date=date(2024, 6, 28),
                ),
            ]
        )
        session.commit()

    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="cls"
    )

    # 1. Curso com turma ACTIVE é bloqueado no DELETE e no PUT {is_active: false}
    del_blocked = await courses_client.delete(
        f"/api/v1/courses/{course_with_active.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert del_blocked.status_code == status.HTTP_409_CONFLICT
    assert del_blocked.json()["message"] == COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE

    put_blocked = await courses_client.put(
        f"/api/v1/courses/{course_with_active.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert put_blocked.status_code == status.HTTP_409_CONFLICT
    assert put_blocked.json()["message"] == COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE

    with db_session_factory() as session:
        still_active = session.scalar(
            select(Course).where(Course.id == course_with_active.id)
        )
        assert still_active is not None
        assert still_active.is_active is True

    # 2. Outros campos ainda podem ser atualizados normalmente mesmo com turma ACTIVE
    put_name_ok = await courses_client.put(
        f"/api/v1/courses/{course_with_active.id}",
        json={"name": "Técnico em Mecânica Avançada", "is_active": True},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert put_name_ok.status_code == status.HTTP_200_OK
    assert put_name_ok.json()["name"] == "Técnico em Mecânica Avançada"

    # 3. Curso apenas com turmas COMPLETED/PLANNING/ARCHIVED pode ser desativado normalmente
    del_allowed = await courses_client.delete(
        f"/api/v1/courses/{course_with_inactive_classes.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert del_allowed.status_code == status.HTTP_200_OK
    assert del_allowed.json()["is_active"] is False

    # Reativar via PUT e desativar novamente via PUT is_active=False também funciona
    reactivate_res = await courses_client.put(
        f"/api/v1/courses/{course_with_inactive_classes.id}",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert reactivate_res.status_code == status.HTTP_200_OK
    assert reactivate_res.json()["is_active"] is True

    put_deactivate_allowed = await courses_client.put(
        f"/api/v1/courses/{course_with_inactive_classes.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert put_deactivate_allowed.status_code == status.HTTP_200_OK
    assert put_deactivate_allowed.json()["is_active"] is False
