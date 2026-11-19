"""Testes unitários e de integração para Endpoints CRUD de Disciplinas do Currículo Técnico (BE-013)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
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
from app.models import AcademicClass, Base, Course, Subject, User
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import ClassStatus, Shift, UserRole
from app.schemas.subject import (
    SubjectCreateSchema,
    validate_subject_code_pt,
    validate_subject_name_pt,
    validate_subject_workload_hours_pt,
)
from app.schemas.user import UserProfileCreateSchema
from app.services.subject_service import (
    SUBJECT_ACTIVATION_INACTIVE_COURSE_MESSAGE,
    SUBJECT_CODE_COURSE_CONFLICT_MESSAGE,
    SUBJECT_COURSE_NOT_FOUND_MESSAGE,
    SUBJECT_INACTIVE_COURSE_MESSAGE,
    SUBJECT_NOT_FOUND_MESSAGE,
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
def subjects_app(
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
async def subjects_client(subjects_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=subjects_app)
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
    """Helper para persistir um curso técnico diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description=description,
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
    syllabus: str | None = None,
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
            syllabus=syllabus,
            is_active=is_active,
        )


def test_subject_orm_validations_and_db_constraints(
    db_session_factory: sessionmaker[Session],
) -> None:
    """Valida restrições unitárias ORM e constraints relacionais no banco (uq e check)."""
    course_1 = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    course_2 = _create_course_in_db(
        db_session_factory,
        code="TEC-ELT-01",
        name="Técnico em Eletromecânica",
    )

    valid_subject = Subject(
        course_id=course_1.id,
        code="  met-dim-01  ",
        name="  Metrologia Dimensional  ",
        workload_hours=80,
        syllabus="  Leitura com paquímetro e micrômetro.  ",
    )
    assert valid_subject.code == "MET-DIM-01"
    assert valid_subject.name == "Metrologia Dimensional"
    assert valid_subject.workload_hours == 80
    assert valid_subject.syllabus == "Leitura com paquímetro e micrômetro."

    blank_syllabus_subject = Subject(
        course_id=course_1.id,
        code="DES-TEC-01",
        name="Desenho Técnico",
        workload_hours=60,
        syllabus="   ",
    )
    assert blank_syllabus_subject.syllabus is None

    with pytest.raises(ValueError, match="entre 2 e 50 caracteres"):
        Subject(course_id=course_1.id, code="A", name="Disciplina Válida", workload_hours=40)

    with pytest.raises(ValueError, match="entre 2 e 50 caracteres"):
        Subject(course_id=course_1.id, code="X" * 51, name="Disciplina Válida", workload_hours=40)

    with pytest.raises(ValueError, match="entre 3 e 150 caracteres"):
        Subject(course_id=course_1.id, code="MT-01", name="AB", workload_hours=40)

    for invalid_hours in (0, -40, True):
        with pytest.raises(ValueError, match="maior que zero"):
            Subject(
                course_id=course_1.id,
                code="MT-01",
                name="Metrologia",
                workload_hours=invalid_hours,  # type: ignore[arg-type]
            )

    # Persistência válida + restrição UNIQUE (course_id, code)
    with db_session_factory() as session:
        session.add(valid_subject)
        session.commit()

    with db_session_factory() as session:
        duplicate_same_course = Subject(
            course_id=course_1.id,
            code="MET-DIM-01",
            name="Outra Disciplina",
            workload_hours=60,
        )
        session.add(duplicate_same_course)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Mesmo código em outro curso deve ser permitido pela constraint composta
    with db_session_factory() as session:
        same_code_other_course = Subject(
            course_id=course_2.id,
            code="MET-DIM-01",
            name="Metrologia Dimensional",
            workload_hours=80,
        )
        session.add(same_code_other_course)
        session.commit()

    # Constraint CHECK (workload_hours > 0) garantida no nível SQL
    with db_session_factory() as session:
        with pytest.raises(IntegrityError):
            session.execute(
                sa.text(
                    "INSERT INTO subjects (id, course_id, code, name, workload_hours, is_active) "
                    "VALUES (:id, :course_id, :code, :name, :workload_hours, :is_active)"
                ),
                {
                    "id": str(uuid4()).replace("-", ""),
                    "course_id": str(course_1.id).replace("-", ""),
                    "code": "CHK-01",
                    "name": "Disciplina Check",
                    "workload_hours": 0,
                    "is_active": True,
                },
            )
            session.commit()
        session.rollback()


def test_pydantic_validators_for_subjects() -> None:
    """Garante validação e normalização de código, nome e carga horária positiva no Pydantic."""
    assert validate_subject_code_pt("  uc-01 ") == "UC-01"
    assert validate_subject_name_pt("  Processos   de   Fabricação  ") == "Processos de Fabricação"
    assert validate_subject_workload_hours_pt(80) == 80
    assert validate_subject_workload_hours_pt("120") == 120

    for invalid_hours in (0, -1, -80, True, False, 40.5, "0", "-10", "abc"):
        with pytest.raises(Exception):
            validate_subject_workload_hours_pt(invalid_hours)

    for invalid_code in ("A", "X" * 51, "MET 01", "<script>"):
        with pytest.raises(Exception):
            validate_subject_code_pt(invalid_code)

    for invalid_name in ("AB", "Y" * 151, "<b>Metrologia</b>"):
        with pytest.raises(Exception):
            validate_subject_name_pt(invalid_name)

    schema = SubjectCreateSchema(
        course_id=uuid4(),
        code="  met-01 ",
        name="  Metrologia   Básica ",
        workload_hours=60,
        syllabus="  Unidade 1: Paquímetro\nUnidade 2: Micrômetro  ",
    )
    assert schema.code == "MET-01"
    assert schema.name == "Metrologia Básica"
    assert schema.workload_hours == 60
    assert schema.syllabus == "Unidade 1: Paquímetro\nUnidade 2: Micrômetro"
    assert schema.is_active is True


async def test_subjects_rbac_enforces_roles_across_endpoints(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante 401 sem autenticação, 403 para STUDENT, leitura para TEACHER e acesso total ADMIN/COORDINATOR."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )

    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="stu"
    )
    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="tch"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="adm"
    )

    post_payload = {
        "course_id": str(course.id),
        "code": "USN-01",
        "name": "Usinagem Convencional",
        "workload_hours": 120,
    }
    put_payload = {"workload_hours": 100}

    all_routes: list[tuple[str, str, dict[str, Any] | None]] = [
        ("GET", "/api/v1/subjects", None),
        ("POST", "/api/v1/subjects", post_payload),
        ("GET", f"/api/v1/subjects/{subject.id}", None),
        ("PUT", f"/api/v1/subjects/{subject.id}", put_payload),
    ]

    for method, url, body in all_routes:
        unauth_res = await subjects_client.request(method, url, json=body)
        assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

        student_res = await subjects_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_res.status_code == status.HTTP_403_FORBIDDEN
        assert student_res.json()["message"] == "Acesso não autorizado para seu perfil"

    # TEACHER pode listar e consultar detalhes, mas não pode criar ou editar
    teacher_list = await subjects_client.get(
        "/api/v1/subjects",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_list.status_code == status.HTTP_200_OK

    teacher_get = await subjects_client.get(
        f"/api/v1/subjects/{subject.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert teacher_get.status_code == status.HTTP_200_OK

    for method, url, body in (
        ("POST", "/api/v1/subjects", post_payload),
        ("PUT", f"/api/v1/subjects/{subject.id}", put_payload),
    ):
        teacher_write = await subjects_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert teacher_write.status_code == status.HTTP_403_FORBIDDEN

    # COORDINATOR e ADMIN têm acesso completo
    coord_post = await subjects_client.post(
        "/api/v1/subjects",
        json=post_payload,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert coord_post.status_code == status.HTTP_201_CREATED
    created_id = coord_post.json()["id"]

    admin_put = await subjects_client.put(
        f"/api/v1/subjects/{created_id}",
        json={"workload_hours": 140},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_put.status_code == status.HTTP_200_OK
    assert admin_put.json()["workload_hours"] == 140


async def test_create_subject_success_normalizes_and_persists_with_syllabus(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: POST cria disciplina vinculada ao curso com ementa técnica e carga horária."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        total_hours=1200,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="c1"
    )

    syllabus_text = (
        "1. Instrumentos de medição linear.\n"
        "2. Tolerâncias dimensionais e geométricas (IT / H7)."
    )
    response = await subjects_client.post(
        "/api/v1/subjects",
        json={
            "course_id": str(course.id),
            "code": "  met-dim-01  ",
            "name": "  Metrologia   Dimensional  ",
            "workload_hours": 80,
            "syllabus": f"  {syllabus_text}  ",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    UUID(body["id"])
    assert body["course_id"] == str(course.id)
    assert body["code"] == "MET-DIM-01"
    assert body["name"] == "Metrologia Dimensional"
    assert body["workload_hours"] == 80
    assert body["syllabus"] == syllabus_text
    assert body["is_active"] is True
    assert body["course"] == {
        "id": str(course.id),
        "code": "TEC-MEC-01",
        "name": "Técnico em Mecânica",
        "total_hours": 1200,
        "is_active": True,
    }
    assert "created_at" in body
    assert "updated_at" in body

    with db_session_factory() as session:
        persisted = session.scalar(
            select(Subject).where(
                Subject.course_id == course.id,
                Subject.code == "MET-DIM-01",
            )
        )
        assert persisted is not None
        assert persisted.name == "Metrologia Dimensional"
        assert persisted.workload_hours == 80
        assert persisted.syllabus == syllabus_text


@pytest.mark.parametrize(
    "invalid_workload",
    [0, -1, -60, False, True, 40.5, "0", "-10", "oitenta"],
)
async def test_create_subject_returns_400_when_workload_hours_non_positive_or_invalid(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    invalid_workload: Any,
) -> None:
    """Critério de Aceitação: HTTP 400 se carga horária for menor ou igual a zero (ou inválida)."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="wl"
    )

    response = await subjects_client.post(
        "/api/v1/subjects",
        json={
            "course_id": str(course.id),
            "code": "MET-01",
            "name": "Metrologia Dimensional",
            "workload_hours": invalid_workload,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert any(item["field"] == "workload_hours" for item in body["details"])


@pytest.mark.parametrize(
    "missing_field",
    ["name", "code", "course_id", "workload_hours"],
)
async def test_create_subject_requires_mandatory_fields_returning_400(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    missing_field: str,
) -> None:
    """Critério de Aceitação: POST exige nome, código, course_id e carga horária positiva."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="req"
    )

    payload: dict[str, Any] = {
        "course_id": str(course.id),
        "code": "MET-01",
        "name": "Metrologia Dimensional",
        "workload_hours": 80,
    }
    payload.pop(missing_field)

    response = await subjects_client.post(
        "/api/v1/subjects",
        json=payload,
        headers={"Authorization": f"Bearer {coord_token}"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert any(item["field"] == missing_field for item in body["details"])


@pytest.mark.parametrize(
    "invalid_payload_override",
    [
        {"code": "A"},
        {"code": "MET 01"},
        {"name": "AB"},
        {"name": "<script>alert(1)</script>"},
        {"syllabus": "<iframe src='x'></iframe>"},
        {"course_id": "uuid-invalido"},
        {"extra_field": "nao-permitido"},
    ],
)
async def test_create_subject_rejects_invalid_or_unsafe_payload_with_400(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
    invalid_payload_override: dict[str, Any],
) -> None:
    """Garante HTTP 400 para código/nome inválidos, XSS, UUID inválido e campos extras."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="inv"
    )

    payload: dict[str, Any] = {
        "course_id": str(course.id),
        "code": "MET-01",
        "name": "Metrologia Dimensional",
        "workload_hours": 80,
        **invalid_payload_override,
    }
    response = await subjects_client.post(
        "/api/v1/subjects",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "VALIDATION_ERROR"


async def test_create_subject_course_validation_and_code_uniqueness_per_course(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida 404 para curso inexistente, 422 para curso inativo, 409 duplicado no curso e 201 em outro curso."""
    active_course_1 = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        is_active=True,
    )
    active_course_2 = _create_course_in_db(
        db_session_factory,
        code="TEC-ELT-01",
        name="Técnico em Eletromecânica",
        is_active=True,
    )
    inactive_course = _create_course_in_db(
        db_session_factory,
        code="TEC-OLD-01",
        name="Curso Desativado",
        is_active=False,
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=active_course_1.id,
        code="MET-01",
        name="Metrologia Dimensional",
        workload_hours=80,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="uniq"
    )

    # 1. Curso inexistente -> 404
    not_found_res = await subjects_client.post(
        "/api/v1/subjects",
        json={
            "course_id": str(uuid4()),
            "code": "MET-01",
            "name": "Metrologia Dimensional",
            "workload_hours": 80,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == SUBJECT_COURSE_NOT_FOUND_MESSAGE

    # 2. Curso inativo -> 422
    inactive_res = await subjects_client.post(
        "/api/v1/subjects",
        json={
            "course_id": str(inactive_course.id),
            "code": "MET-01",
            "name": "Metrologia Dimensional",
            "workload_hours": 80,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert inactive_res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert inactive_res.json()["message"] == SUBJECT_INACTIVE_COURSE_MESSAGE

    # 3. Código duplicado no mesmo curso (case-insensitive) -> 409
    for dup_code in ("MET-01", "  met-01  "):
        dup_res = await subjects_client.post(
            "/api/v1/subjects",
            json={
                "course_id": str(active_course_1.id),
                "code": dup_code,
                "name": "Metrologia Duplicada",
                "workload_hours": 60,
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert dup_res.status_code == status.HTTP_409_CONFLICT
        assert dup_res.json()["message"] == SUBJECT_CODE_COURSE_CONFLICT_MESSAGE

    # 4. Mesmo código em outro curso ativo -> 201
    other_course_res = await subjects_client.post(
        "/api/v1/subjects",
        json={
            "course_id": str(active_course_2.id),
            "code": "MET-01",
            "name": "Metrologia Aplicada",
            "workload_hours": 80,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert other_course_res.status_code == status.HTTP_201_CREATED
    assert other_course_res.json()["course_id"] == str(active_course_2.id)


async def test_list_subjects_supports_course_id_is_active_search_and_pagination(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios de Aceitação: Listagem paginada com filtro por course_id, is_active e busca textual."""
    course_mec = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    course_ads = _create_course_in_db(
        db_session_factory,
        code="TEC-ADS-01",
        name="Técnico em Desenvolvimento de Sistemas",
    )

    # Múltiplas turmas do mesmo curso compartilham as disciplinas vinculadas ao curso
    with db_session_factory() as session:
        class_repo = AcademicClassRepository(session=session)
        class_repo.create(
            course_id=course_mec.id,
            code="MEC-2026-1M",
            period="2026.1",
            shift=Shift.MORNING,
            max_students=40,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )
        class_repo.create(
            course_id=course_mec.id,
            code="MEC-2026-1N",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=40,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )

    _create_subject_in_db(
        db_session_factory,
        course_id=course_mec.id,
        code="MET-01",
        name="Metrologia Dimensional",
        workload_hours=80,
        syllabus="Paquímetro, micrômetro e 100% de tolerância IT_01.",
        is_active=True,
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=course_mec.id,
        code="USN-01",
        name="Processos de Usinagem",
        workload_hours=120,
        syllabus="Tornearia cilíndrica e fresamento.",
        is_active=True,
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=course_mec.id,
        code="DES-OLD",
        name="Desenho Manual Legado",
        workload_hours=40,
        syllabus="Prancheta técnica descontinuada.",
        is_active=False,
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=course_ads.id,
        code="LOG-01",
        name="Lógica de Programação",
        workload_hours=100,
        syllabus="Algoritmos estruturados e Python.",
        is_active=True,
    )

    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="lst"
    )

    # 1. Listagem geral paginada (ordenação name ASC)
    all_res = await subjects_client.get(
        "/api/v1/subjects?page=1&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert all_res.status_code == status.HTTP_200_OK
    all_body = all_res.json()
    assert all_body["total"] == 4
    assert all_body["page"] == 1
    assert all_body["limit"] == 2
    assert [item["code"] for item in all_body["data"]] == ["DES-OLD", "LOG-01"]

    page_2_res = await subjects_client.get(
        "/api/v1/subjects?page=2&limit=2",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert page_2_res.status_code == status.HTTP_200_OK
    assert [item["code"] for item in page_2_res.json()["data"]] == ["MET-01", "USN-01"]

    # 2. Filtro por course_id (retorna todas as disciplinas do curso compartilhadas entre turmas)
    by_course_res = await subjects_client.get(
        f"/api/v1/subjects?course_id={course_mec.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert by_course_res.status_code == status.HTTP_200_OK
    assert by_course_res.json()["total"] == 3
    assert {item["code"] for item in by_course_res.json()["data"]} == {
        "MET-01",
        "USN-01",
        "DES-OLD",
    }

    # 3. Filtro por apenas disciplinas ativas (is_active=true) e inativas (is_active=false)
    active_only_res = await subjects_client.get(
        "/api/v1/subjects?is_active=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert active_only_res.status_code == status.HTTP_200_OK
    assert active_only_res.json()["total"] == 3
    assert all(item["is_active"] is True for item in active_only_res.json()["data"])

    inactive_only_res = await subjects_client.get(
        "/api/v1/subjects?is_active=false",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert inactive_only_res.status_code == status.HTTP_200_OK
    assert inactive_only_res.json()["total"] == 1
    assert inactive_only_res.json()["data"][0]["code"] == "DES-OLD"

    # 4. Combinação course_id + is_active=true
    course_active_res = await subjects_client.get(
        f"/api/v1/subjects?course_id={course_mec.id}&is_active=true",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert course_active_res.status_code == status.HTTP_200_OK
    assert course_active_res.json()["total"] == 2
    assert [item["code"] for item in course_active_res.json()["data"]] == ["MET-01", "USN-01"]

    # 5. Busca textual por ementa/nome/código incluindo caracteres curinga escapados (% e _)
    search_syllabus_res = await subjects_client.get(
        "/api/v1/subjects?search=tornearia",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_syllabus_res.status_code == status.HTTP_200_OK
    assert search_syllabus_res.json()["total"] == 1
    assert search_syllabus_res.json()["data"][0]["code"] == "USN-01"

    search_wildcard_res = await subjects_client.get(
        "/api/v1/subjects?search=100%25",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_wildcard_res.status_code == status.HTTP_200_OK
    assert search_wildcard_res.json()["total"] == 1
    assert search_wildcard_res.json()["data"][0]["code"] == "MET-01"

    search_underscore_res = await subjects_client.get(
        "/api/v1/subjects?search=IT_01",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert search_underscore_res.status_code == status.HTTP_200_OK
    assert search_underscore_res.json()["total"] == 1
    assert search_underscore_res.json()["data"][0]["code"] == "MET-01"


async def test_get_subject_by_id_returns_details_or_404_and_400(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/subjects/{id} retornando 200 com curso, 404 se inexistente e 400 se UUID inválido."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        total_hours=1200,
    )
    subject = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-01",
        name="Metrologia Dimensional",
        workload_hours=80,
        syllabus="Calibração e medição com micrômetro centesimal.",
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="get"
    )

    ok_res = await subjects_client.get(
        f"/api/v1/subjects/{subject.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert ok_res.status_code == status.HTTP_200_OK
    body = ok_res.json()
    assert body["id"] == str(subject.id)
    assert body["course_id"] == str(course.id)
    assert body["code"] == "MET-01"
    assert body["name"] == "Metrologia Dimensional"
    assert body["workload_hours"] == 80
    assert body["syllabus"] == "Calibração e medição com micrômetro centesimal."
    assert body["is_active"] is True
    assert body["course"]["code"] == "TEC-MEC-01"

    not_found_res = await subjects_client.get(
        f"/api/v1/subjects/{uuid4()}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == SUBJECT_NOT_FOUND_MESSAGE

    bad_uuid_res = await subjects_client.get(
        "/api/v1/subjects/not-a-uuid",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert bad_uuid_res.status_code == status.HTTP_400_BAD_REQUEST
    assert bad_uuid_res.json()["error"] == "VALIDATION_ERROR"


async def test_update_subject_supports_partial_updates_course_transfer_and_validations(
    subjects_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida PUT /api/v1/subjects/{id}: campos, ementa, carga horária <= 0 (400), curso e conflitos."""
    course_1 = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        is_active=True,
    )
    course_2 = _create_course_in_db(
        db_session_factory,
        code="TEC-ELT-01",
        name="Técnico em Eletromecânica",
        is_active=True,
    )
    inactive_course = _create_course_in_db(
        db_session_factory,
        code="TEC-OLD-01",
        name="Curso Inativo",
        is_active=False,
    )

    subject_1 = _create_subject_in_db(
        db_session_factory,
        course_id=course_1.id,
        code="MET-01",
        name="Metrologia Dimensional",
        workload_hours=80,
        syllabus="Ementa inicial.",
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=course_1.id,
        code="USN-01",
        name="Usinagem Convencional",
        workload_hours=120,
    )
    _create_subject_in_db(
        db_session_factory,
        course_id=course_2.id,
        code="ELM-01",
        name="Comandos Elétricos",
        workload_hours=100,
    )
    subject_in_inactive_course = _create_subject_in_db(
        db_session_factory,
        course_id=inactive_course.id,
        code="OLD-01",
        name="Disciplina Antiga",
        workload_hours=40,
        is_active=False,
    )

    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="upd"
    )

    # 1. Atualização mantendo o próprio código e limpando ementa com null
    ok_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={
            "code": "  met-01  ",
            "name": "Metrologia Dimensional Avançada",
            "workload_hours": 100,
            "syllabus": None,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert ok_res.status_code == status.HTTP_200_OK
    ok_body = ok_res.json()
    assert ok_body["code"] == "MET-01"
    assert ok_body["name"] == "Metrologia Dimensional Avançada"
    assert ok_body["workload_hours"] == 100
    assert ok_body["syllabus"] is None

    # 2. HTTP 400 se carga horária <= 0 na atualização
    for invalid_wl in (0, -20):
        wl_res = await subjects_client.put(
            f"/api/v1/subjects/{subject_1.id}",
            json={"workload_hours": invalid_wl},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert wl_res.status_code == status.HTTP_400_BAD_REQUEST
        assert wl_res.json()["error"] == "VALIDATION_ERROR"

    # 3. Conflito 409 ao tentar alterar código para outro já existente no mesmo curso
    conflict_code_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"code": "USN-01"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert conflict_code_res.status_code == status.HTTP_409_CONFLICT
    assert conflict_code_res.json()["message"] == SUBJECT_CODE_COURSE_CONFLICT_MESSAGE

    # 4. Transferência para outro curso ativo atualiza course_id e objeto course retornado
    transfer_ok_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"course_id": str(course_2.id), "syllabus": "Nova ementa eletromecânica."},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert transfer_ok_res.status_code == status.HTTP_200_OK
    transfer_body = transfer_ok_res.json()
    assert transfer_body["course_id"] == str(course_2.id)
    assert transfer_body["course"]["id"] == str(course_2.id)
    assert transfer_body["course"]["code"] == "TEC-ELT-01"
    assert transfer_body["syllabus"] == "Nova ementa eletromecânica."

    # 5. Conflito 409 ao transferir mantendo/alterando para código já existente no curso destino
    transfer_conflict_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"code": "ELM-01"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert transfer_conflict_res.status_code == status.HTTP_409_CONFLICT

    # 6. Transferência para curso inexistente (404) ou inativo (422)
    transfer_404 = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"course_id": str(uuid4())},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert transfer_404.status_code == status.HTTP_404_NOT_FOUND
    assert transfer_404.json()["message"] == SUBJECT_COURSE_NOT_FOUND_MESSAGE

    transfer_422 = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"course_id": str(inactive_course.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert transfer_422.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert transfer_422.json()["message"] == SUBJECT_INACTIVE_COURSE_MESSAGE

    # 7. Desativar e reativar em curso ativo funciona; reativar em curso inativo retorna 422
    deactivate_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert deactivate_res.status_code == status.HTTP_200_OK
    assert deactivate_res.json()["is_active"] is False

    reactivate_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert reactivate_res.status_code == status.HTTP_200_OK
    assert reactivate_res.json()["is_active"] is True

    reactivate_inactive_course = await subjects_client.put(
        f"/api/v1/subjects/{subject_in_inactive_course.id}",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert reactivate_inactive_course.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert reactivate_inactive_course.json()["message"] == SUBJECT_ACTIVATION_INACTIVE_COURSE_MESSAGE

    # 8. Payload vazio e null em campos não-nuláveis retornam 400
    empty_res = await subjects_client.put(
        f"/api/v1/subjects/{subject_1.id}",
        json={},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert empty_res.status_code == status.HTTP_400_BAD_REQUEST

    for non_nullable_field in ("course_id", "code", "name", "workload_hours", "is_active"):
        null_res = await subjects_client.put(
            f"/api/v1/subjects/{subject_1.id}",
            json={non_nullable_field: None},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert null_res.status_code == status.HTTP_400_BAD_REQUEST

    # 9. Disciplina inexistente retorna 404
    not_found_res = await subjects_client.put(
        f"/api/v1/subjects/{uuid4()}",
        json={"name": "Disciplina Nova"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert not_found_res.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_res.json()["message"] == SUBJECT_NOT_FOUND_MESSAGE
