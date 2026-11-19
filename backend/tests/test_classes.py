"""Testes unitários e de integração para Endpoints CRUD de Turmas Acadêmicas e Períodos Letivos (BE-012)."""

from collections.abc import AsyncIterator, Generator
from datetime import date, datetime
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
from app.models import AcademicClass, Base, Course, User
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.academic_class import (
    AcademicClassCreateSchema,
    validate_iso_date_pt,
    validate_max_students_pt,
)
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.academic_class_service import (
    CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE,
    CLASS_CODE_PERIOD_CONFLICT_MESSAGE,
    CLASS_COURSE_NOT_FOUND_MESSAGE,
    CLASS_INACTIVE_COURSE_MESSAGE,
    CLASS_NOT_FOUND_MESSAGE,
    CLASS_REOPEN_FORBIDDEN_MESSAGE,
    CLASS_TEACHER_FORBIDDEN_MESSAGE,
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
def classes_app(
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
async def classes_client(classes_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=classes_app)
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


def _create_class_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str,
    period: str = "2026.1",
    shift: Shift = Shift.MORNING,
    max_students: int = 40,
    status_value: ClassStatus = ClassStatus.PLANNING,
    start_date: date = date(2026, 2, 2),
    end_date: date = date(2026, 6, 30),
) -> AcademicClass:
    """Helper para persistir uma turma acadêmica diretamente via repositório."""
    with session_factory() as session:
        repo = AcademicClassRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            period=period,
            shift=shift,
            max_students=max_students,
            status=status_value,
            start_date=start_date,
            end_date=end_date,
        )


def _create_auxiliary_enrollments_table(engine: sa.Engine) -> sa.Table:
    """Cria tabela auxiliar 'enrollments' em MetaData separada para validar contagem de vagas."""
    aux_metadata = sa.MetaData()
    enrollments_table = sa.Table(
        "enrollments",
        aux_metadata,
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("student_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("class_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
    )
    aux_metadata.create_all(bind=engine)
    return enrollments_table


def _create_auxiliary_teacher_assignments_table(engine: sa.Engine) -> sa.Table:
    """Cria tabela auxiliar 'teacher_assignments' para validar acesso contextual de docentes."""
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


def test_academic_class_orm_validations_and_db_constraints(
    db_session_factory: sessionmaker[Session],
) -> None:
    """Valida restrições unitárias ORM e constraints relacionais no banco (uq e check)."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )

    valid_cls = AcademicClass(
        course_id=course.id,
        code="  mec-2026-1t  ",
        period="  2026.1  ",
        shift=Shift.MORNING,
        max_students=40,
        status=ClassStatus.PLANNING,
        start_date=date(2026, 2, 2),
        end_date=date(2026, 6, 30),
    )
    assert valid_cls.code == "MEC-2026-1T"
    assert valid_cls.period == "2026.1"

    with pytest.raises(ValueError, match="entre 3 e 40 caracteres"):
        AcademicClass(
            course_id=course.id,
            code="AB",
            period="2026.1",
            shift=Shift.MORNING,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )

    with pytest.raises(ValueError, match="entre 3 e 20 caracteres"):
        AcademicClass(
            course_id=course.id,
            code="MEC-2026-1T",
            period="26",
            shift=Shift.MORNING,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )

    for invalid_max in (0, 101, True):
        with pytest.raises(ValueError, match="entre 1 e 100"):
            AcademicClass(
                course_id=course.id,
                code="MEC-2026-1T",
                period="2026.1",
                shift=Shift.MORNING,
                max_students=invalid_max,  # type: ignore[arg-type]
                start_date=date(2026, 2, 2),
                end_date=date(2026, 6, 30),
            )

    with pytest.raises(ValueError, match="objetos date válidos"):
        AcademicClass(
            course_id=course.id,
            code="MEC-2026-1T",
            period="2026.1",
            shift=Shift.MORNING,
            start_date=datetime(2026, 2, 2, 8, 0),
            end_date=date(2026, 6, 30),
        )

    # Constraint UNIQUE (code, period) e CHECK (start_date < end_date) no banco
    with db_session_factory() as session:
        session.add(valid_cls)
        session.commit()

    with db_session_factory() as session:
        duplicate_cls = AcademicClass(
            course_id=course.id,
            code="MEC-2026-1T",
            period="2026.1",
            shift=Shift.NIGHT,
            max_students=30,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )
        session.add(duplicate_cls)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    with db_session_factory() as session:
        invalid_range_cls = AcademicClass(
            course_id=course.id,
            code="MEC-2026-2T",
            period="2026.2",
            shift=Shift.AFTERNOON,
            max_students=30,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 10),
        )
        session.add(invalid_range_cls)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_pydantic_validators_for_dates_and_capacity() -> None:
    """Garante validação estrita de datas puras, capacidade e range start_date < end_date."""
    assert validate_iso_date_pt("2026-02-02") == date(2026, 2, 2)
    assert validate_iso_date_pt(date(2026, 2, 2)) == date(2026, 2, 2)
    assert validate_max_students_pt("35") == 35

    for invalid_date in (
        datetime(2026, 2, 2, 8, 0),
        True,
        123,
        12.5,
        "2026-02-30",
        "02/02/2026",
        "2026-02-02T00:00:00Z",
    ):
        with pytest.raises(Exception):
            validate_iso_date_pt(invalid_date)

    schema = AcademicClassCreateSchema(
        course_id=uuid4(),
        code="  mec-2026-1t ",
        period=" 2026/1 ",
        shift=Shift.NIGHT,
        start_date="2026-02-02",  # type: ignore[arg-type]
        end_date="2026-06-30",  # type: ignore[arg-type]
    )
    assert schema.code == "MEC-2026-1T"
    assert schema.period == "2026/1"
    assert schema.max_students == 40
    assert schema.status == ClassStatus.PLANNING


async def test_classes_rbac_blocks_unauthenticated_student_and_teacher_writes(
    classes_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida RBAC: 401 sem token, 403 para STUDENT em tudo e 403 para TEACHER em mutações."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
    )
    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="stu1"
    )
    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="tch1"
    )

    create_payload = {
        "course_id": str(course.id),
        "code": "MEC-2026-2T",
        "period": "2026.2",
        "shift": Shift.AFTERNOON.value,
        "start_date": "2026-08-03",
        "end_date": "2026-12-18",
    }
    all_routes: list[tuple[str, str, dict[str, Any] | None]] = [
        ("GET", "/api/v1/classes", None),
        ("POST", "/api/v1/classes", create_payload),
        ("GET", f"/api/v1/classes/{academic_class.id}", None),
        ("PATCH", f"/api/v1/classes/{academic_class.id}/status", {"status": "ACTIVE"}),
    ]

    for method, url, body in all_routes:
        unauth_res = await classes_client.request(method, url, json=body)
        assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

        student_res = await classes_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert student_res.status_code == status.HTTP_403_FORBIDDEN
        assert student_res.json()["error"] == "FORBIDDEN"

    for method, url, body in (
        ("POST", "/api/v1/classes", create_payload),
        ("PATCH", f"/api/v1/classes/{academic_class.id}/status", {"status": "ACTIVE"}),
    ):
        teacher_write_res = await classes_client.request(
            method,
            url,
            json=body,
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert teacher_write_res.status_code == status.HTTP_403_FORBIDDEN
        assert teacher_write_res.json()["error"] == "FORBIDDEN"


async def test_teacher_contextual_access_without_and_with_assignments(
    classes_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Observação Técnica: Professores consultam apenas turmas onde lecionam sem permissão global."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    class_a = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        period="2026.1",
        shift=Shift.MORNING,
        status_value=ClassStatus.ACTIVE,
    )
    class_b = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-2T",
        period="2026.2",
        shift=Shift.NIGHT,
        status_value=ClassStatus.PLANNING,
    )
    teacher_user, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ctx1"
    )
    other_teacher, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="ctx2"
    )

    # 1. Fail-closed antes da tabela teacher_assignments existir
    list_no_table = await classes_client.get(
        "/api/v1/classes",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_no_table.status_code == status.HTTP_200_OK
    assert list_no_table.json() == {"data": [], "total": 0, "page": 1, "limit": 20}

    detail_no_table = await classes_client.get(
        f"/api/v1/classes/{class_a.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert detail_no_table.status_code == status.HTTP_403_FORBIDDEN
    assert detail_no_table.json()["message"] == CLASS_TEACHER_FORBIDDEN_MESSAGE

    not_found_no_table = await classes_client.get(
        f"/api/v1/classes/{uuid4()}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert not_found_no_table.status_code == status.HTTP_404_NOT_FOUND
    assert not_found_no_table.json()["message"] == CLASS_NOT_FOUND_MESSAGE

    # 2. Com teacher_assignments: múltiplas disciplinas na mesma turma não duplicam a turma
    ta_table = _create_auxiliary_teacher_assignments_table(db_engine)
    with db_engine.begin() as conn:
        conn.execute(
            ta_table.insert(),
            [
                {
                    "id": uuid4(),
                    "teacher_id": teacher_user.id,
                    "class_id": class_a.id,
                    "subject_id": uuid4(),
                },
                {
                    "id": uuid4(),
                    "teacher_id": teacher_user.id,
                    "class_id": class_a.id,
                    "subject_id": uuid4(),
                },
                {
                    "id": uuid4(),
                    "teacher_id": other_teacher.id,
                    "class_id": class_b.id,
                    "subject_id": uuid4(),
                },
            ],
        )

    list_assigned = await classes_client.get(
        "/api/v1/classes",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_assigned.status_code == status.HTTP_200_OK
    list_body = list_assigned.json()
    assert list_body["total"] == 1
    assert len(list_body["data"]) == 1
    assert list_body["data"][0]["id"] == str(class_a.id)

    # Filtros combinados respeitam o escopo do docente
    list_filtered_none = await classes_client.get(
        "/api/v1/classes?shift=NIGHT",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_filtered_none.status_code == status.HTTP_200_OK
    assert list_filtered_none.json()["total"] == 0

    list_filtered_match = await classes_client.get(
        f"/api/v1/classes?course_id={course.id}&period=2026.1&shift=MORNING&status=ACTIVE",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert list_filtered_match.status_code == status.HTTP_200_OK
    assert list_filtered_match.json()["total"] == 1

    # Detalhe permitido apenas para a turma alocada
    detail_allowed = await classes_client.get(
        f"/api/v1/classes/{class_a.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert detail_allowed.status_code == status.HTTP_200_OK
    assert detail_allowed.json()["code"] == "MEC-2026-1T"

    detail_forbidden = await classes_client.get(
        f"/api/v1/classes/{class_b.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert detail_forbidden.status_code == status.HTTP_403_FORBIDDEN
    assert detail_forbidden.json()["message"] == CLASS_TEACHER_FORBIDDEN_MESSAGE


async def test_create_class_success_defaults_and_business_validations(
    classes_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios de Aceitação: criação vinculada a curso, 404 curso inválido, 422 inativo, 409 duplicado."""
    active_course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        total_hours=1200,
        is_active=True,
    )
    inactive_course = _create_course_in_db(
        db_session_factory,
        code="TEC-LOG-01",
        name="Técnico em Logística",
        total_hours=800,
        is_active=False,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crt1"
    )

    # 1. Criação com defaults (max_students=40, status=PLANNING) e normalização
    res_ok = await classes_client.post(
        "/api/v1/classes",
        json={
            "course_id": str(active_course.id),
            "code": "  mec-2026-1t  ",
            "period": "  2026.1  ",
            "shift": "MORNING",
            "start_date": "2026-02-02",
            "end_date": "2026-06-30",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_ok.status_code == status.HTTP_201_CREATED
    body = res_ok.json()
    UUID(body["id"])
    assert body["course_id"] == str(active_course.id)
    assert body["code"] == "MEC-2026-1T"
    assert body["period"] == "2026.1"
    assert body["shift"] == "MORNING"
    assert body["max_students"] == 40
    assert body["enrolled_students_count"] == 0
    assert body["available_slots"] == 40
    assert body["status"] == "PLANNING"
    assert body["start_date"] == "2026-02-02"
    assert body["end_date"] == "2026-06-30"
    assert body["course"] == {
        "id": str(active_course.id),
        "code": "TEC-MEC-01",
        "name": "Técnico em Mecânica",
        "total_hours": 1200,
        "is_active": True,
    }

    with db_session_factory() as session:
        persisted = session.scalar(
            select(AcademicClass).where(AcademicClass.id == UUID(body["id"]))
        )
        assert persisted is not None
        assert persisted.code == "MEC-2026-1T"

    # 2. Mesmo código em período letivo diferente é permitido (201)
    res_diff_period = await classes_client.post(
        "/api/v1/classes",
        json={
            "course_id": str(active_course.id),
            "code": "MEC-2026-1T",
            "period": "2026.2",
            "shift": "AFTERNOON",
            "max_students": 32,
            "status": "ACTIVE",
            "start_date": "2026-08-03",
            "end_date": "2026-12-18",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_diff_period.status_code == status.HTTP_201_CREATED
    assert res_diff_period.json()["max_students"] == 32
    assert res_diff_period.json()["available_slots"] == 32
    assert res_diff_period.json()["status"] == "ACTIVE"

    # 3. Duplicidade de (code, period) case-insensitive retorna 409
    res_conflict = await classes_client.post(
        "/api/v1/classes",
        json={
            "course_id": str(active_course.id),
            "code": "mec-2026-1t",
            "period": "2026.1",
            "shift": "NIGHT",
            "start_date": "2026-02-02",
            "end_date": "2026-06-30",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_conflict.status_code == status.HTTP_409_CONFLICT
    assert res_conflict.json()["message"] == CLASS_CODE_PERIOD_CONFLICT_MESSAGE

    # 4. Curso inexistente retorna HTTP 404
    res_course_404 = await classes_client.post(
        "/api/v1/classes",
        json={
            "course_id": str(uuid4()),
            "code": "MEC-2026-9T",
            "period": "2026.1",
            "shift": "MORNING",
            "start_date": "2026-02-02",
            "end_date": "2026-06-30",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_course_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_course_404.json()["message"] == CLASS_COURSE_NOT_FOUND_MESSAGE

    # 5. Curso inativo retorna HTTP 422
    res_inactive_422 = await classes_client.post(
        "/api/v1/classes",
        json={
            "course_id": str(inactive_course.id),
            "code": "LOG-2026-1T",
            "period": "2026.1",
            "shift": "NIGHT",
            "start_date": "2026-02-02",
            "end_date": "2026-06-30",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_422.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_inactive_422.json()["message"] == CLASS_INACTIVE_COURSE_MESSAGE


@pytest.mark.parametrize(
    "invalid_overrides",
    [
        {"start_date": "2026-06-30", "end_date": "2026-06-30"},
        {"start_date": "2026-07-01", "end_date": "2026-06-30"},
        {"start_date": "02/02/2026"},
        {"start_date": "2026-02-30"},
        {"start_date": "2026-02-02T08:00:00Z"},
        {"end_date": True},
        {"end_date": 20260630},
        {"max_students": 0},
        {"max_students": -5},
        {"max_students": 101},
        {"max_students": True},
        {"code": "AB"},
        {"code": "MEC 2026"},
        {"code": "<script>alert(1)</script>"},
        {"period": "26"},
        {"period": "2026 1"},
        {"shift": "DAWN"},
        {"status": "UNKNOWN"},
        {"extra_field": "forbidden"},
    ],
)
async def test_create_class_rejects_invalid_pydantic_payloads(
    invalid_overrides: dict[str, Any],
    classes_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: validação Pydantic de start_date < end_date e rejeição de entradas inválidas."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="val1"
    )

    payload: dict[str, Any] = {
        "course_id": str(course.id),
        "code": "MEC-2026-1T",
        "period": "2026.1",
        "shift": "MORNING",
        "max_students": 40,
        "start_date": "2026-02-02",
        "end_date": "2026-06-30",
    }
    payload.update(invalid_overrides)

    res = await classes_client.post(
        "/api/v1/classes",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert res.json()["error"] == "VALIDATION_ERROR"


async def test_list_classes_filters_pagination_search_and_enrollment_counts(
    classes_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida GET /api/v1/classes com filtros, paginação, ordenação, busca e contagem em lote."""
    mec_course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Mecânica de Precisão 100% Prática",
    )
    ads_course = _create_course_in_db(
        db_session_factory,
        code="TEC-ADS-01",
        name="Análise e Desenvolvimento de Sistemas",
    )

    cls_1 = _create_class_in_db(
        db_session_factory,
        course_id=mec_course.id,
        code="MEC-2026-1T",
        period="2026.1",
        shift=Shift.MORNING,
        max_students=3,
        status_value=ClassStatus.ACTIVE,
    )
    cls_2 = _create_class_in_db(
        db_session_factory,
        course_id=ads_course.id,
        code="ADS-2026-1N",
        period="2026.1",
        shift=Shift.NIGHT,
        max_students=35,
        status_value=ClassStatus.PLANNING,
    )
    cls_3 = _create_class_in_db(
        db_session_factory,
        course_id=mec_course.id,
        code="MEC-2025-2V",
        period="2025.2",
        shift=Shift.AFTERNOON,
        max_students=40,
        status_value=ClassStatus.COMPLETED,
    )

    # Popula enrollments com diferentes status para validar contagem apenas de ACTIVE
    enrollments_tbl = _create_auxiliary_enrollments_table(db_engine)
    with db_engine.begin() as conn:
        conn.execute(
            enrollments_tbl.insert(),
            [
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": cls_1.id,
                    "status": EnrollmentStatus.ACTIVE.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": cls_1.id,
                    "status": EnrollmentStatus.ACTIVE.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": cls_1.id,
                    "status": EnrollmentStatus.DROPPED.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": cls_1.id,
                    "status": EnrollmentStatus.SUSPENDED.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": cls_3.id,
                    "status": EnrollmentStatus.COMPLETED.value,
                },
            ],
        )

    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="lst1"
    )

    # 1. Paginação e ordenação (period desc, code asc) + contagem em lote
    page1_res = await classes_client.get(
        "/api/v1/classes?page=1&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page1_res.status_code == status.HTTP_200_OK
    p1 = page1_res.json()
    assert set(p1.keys()) == {"data", "total", "page", "limit"}
    assert p1["total"] == 3
    assert p1["page"] == 1
    assert p1["limit"] == 2
    assert [item["code"] for item in p1["data"]] == ["ADS-2026-1N", "MEC-2026-1T"]
    assert p1["data"][0]["enrolled_students_count"] == 0
    assert p1["data"][0]["available_slots"] == 35
    assert p1["data"][1]["enrolled_students_count"] == 2
    assert p1["data"][1]["max_students"] == 3
    assert p1["data"][1]["available_slots"] == 1

    page2_res = await classes_client.get(
        "/api/v1/classes?page=2&limit=2",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert page2_res.status_code == status.HTTP_200_OK
    p2 = page2_res.json()
    assert [item["code"] for item in p2["data"]] == ["MEC-2025-2V"]
    assert p2["data"][0]["enrolled_students_count"] == 0

    # 2. Filtros por curso, período letivo (case-insensitive), turno e status
    by_course = await classes_client.get(
        f"/api/v1/classes?course_id={mec_course.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert by_course.status_code == status.HTTP_200_OK
    assert by_course.json()["total"] == 2

    by_period = await classes_client.get(
        "/api/v1/classes?period=2026.1",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert by_period.status_code == status.HTTP_200_OK
    assert by_period.json()["total"] == 2

    by_shift = await classes_client.get(
        "/api/v1/classes?shift=NIGHT",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert by_shift.status_code == status.HTTP_200_OK
    assert [item["id"] for item in by_shift.json()["data"]] == [str(cls_2.id)]

    by_status = await classes_client.get(
        "/api/v1/classes?status=COMPLETED",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert by_status.status_code == status.HTTP_200_OK
    assert [item["id"] for item in by_status.json()["data"]] == [str(cls_3.id)]

    # 3. Busca textual (incluindo curinga '%' escapado e busca no curso vinculado)
    search_wildcard = await classes_client.get(
        "/api/v1/classes",
        params={"search": "100%"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_wildcard.status_code == status.HTTP_200_OK
    assert search_wildcard.json()["total"] == 2

    search_course_code = await classes_client.get(
        "/api/v1/classes?search=tec-ads",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert search_course_code.status_code == status.HTTP_200_OK
    assert [item["id"] for item in search_course_code.json()["data"]] == [str(cls_2.id)]

    # 4. Query params inválidos retornam HTTP 400
    for bad_query in (
        "/api/v1/classes?page=0",
        "/api/v1/classes?limit=101",
        "/api/v1/classes?shift=INVALID",
        "/api/v1/classes?status=INVALID",
        "/api/v1/classes?course_id=nao-eh-uuid",
        "/api/v1/classes?extra_param=1",
    ):
        bad_res = await classes_client.get(
            bad_query,
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert bad_res.status_code == status.HTTP_400_BAD_REQUEST


async def test_get_class_detail_enrollment_counts_and_errors(
    classes_client: AsyncClient,
    db_engine: sa.Engine,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: GET /api/v1/classes/{id} com curso e contagem de matriculados vs max_students."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        total_hours=1200,
    )
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        max_students=2,
        status_value=ClassStatus.ACTIVE,
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="det1"
    )

    # 1. Sem tabela enrollments ainda: retorna 0 matriculados e 2 vagas disponíveis
    res_no_table = await classes_client.get(
        f"/api/v1/classes/{academic_class.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_no_table.status_code == status.HTTP_200_OK
    body_no_table = res_no_table.json()
    assert body_no_table["enrolled_students_count"] == 0
    assert body_no_table["max_students"] == 2
    assert body_no_table["available_slots"] == 2
    assert body_no_table["course"]["code"] == "TEC-MEC-01"

    # 2. Com matrículas mistas até lotar (e mesmo se houver excesso, available_slots nunca é negativo)
    enrollments_tbl = _create_auxiliary_enrollments_table(db_engine)
    with db_engine.begin() as conn:
        conn.execute(
            enrollments_tbl.insert(),
            [
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": academic_class.id,
                    "status": EnrollmentStatus.ACTIVE.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": academic_class.id,
                    "status": EnrollmentStatus.ACTIVE.value,
                },
                {
                    "id": uuid4(),
                    "student_id": uuid4(),
                    "class_id": academic_class.id,
                    "status": EnrollmentStatus.DROPPED.value,
                },
            ],
        )

    res_full = await classes_client.get(
        f"/api/v1/classes/{academic_class.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_full.status_code == status.HTTP_200_OK
    body_full = res_full.json()
    assert body_full["enrolled_students_count"] == 2
    assert body_full["max_students"] == 2
    assert body_full["available_slots"] == 0

    # 3. 404 para UUID inexistente e 400 para UUID malformado
    res_404 = await classes_client.get(
        f"/api/v1/classes/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == CLASS_NOT_FOUND_MESSAGE

    res_400 = await classes_client.get(
        "/api/v1/classes/nao-eh-uuid",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_400.status_code == status.HTTP_400_BAD_REQUEST


async def test_patch_class_status_transitions_reopen_governance_and_errors(
    classes_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida PATCH /api/v1/classes/{id}/status com transições, idempotência e reabertura por ADMIN."""
    course = _create_course_in_db(
        db_session_factory,
        code="TEC-MEC-01",
        name="Técnico em Mecânica",
        is_active=True,
    )
    cls_lifecycle = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        period="2026.1",
        status_value=ClassStatus.PLANNING,
    )
    cls_planning_to_archive = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-2T",
        period="2026.2",
        status_value=ClassStatus.PLANNING,
    )
    cls_active_to_archive = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-3T",
        period="2026.3",
        status_value=ClassStatus.ACTIVE,
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="st_crd"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="st_adm"
    )

    # 1. PLANNING -> ACTIVE (COORDINATOR)
    res_active = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_active.status_code == status.HTTP_200_OK
    assert res_active.json()["status"] == "ACTIVE"

    # Idempotência: ACTIVE -> ACTIVE
    res_idem = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_idem.status_code == status.HTTP_200_OK
    assert res_idem.json()["status"] == "ACTIVE"

    # Transição inválida: ACTIVE -> PLANNING retorna 422 INVALID_STATUS_TRANSITION
    res_back_to_planning = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "PLANNING"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_back_to_planning.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_back_to_planning.json()["error"] == "INVALID_STATUS_TRANSITION"

    # 2. ACTIVE -> COMPLETED (COORDINATOR)
    res_completed = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_completed.status_code == status.HTTP_200_OK
    assert res_completed.json()["status"] == "COMPLETED"

    # 3. Reabertura COMPLETED -> ACTIVE: bloqueada para COORDINATOR (403) e permitida para ADMIN (200)
    res_reopen_coord = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_reopen_coord.status_code == status.HTTP_403_FORBIDDEN
    assert res_reopen_coord.json()["message"] == CLASS_REOPEN_FORBIDDEN_MESSAGE

    res_reopen_admin = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_reopen_admin.status_code == status.HTTP_200_OK
    assert res_reopen_admin.json()["status"] == "ACTIVE"

    # 4. COMPLETED -> ARCHIVED e reabertura ARCHIVED -> ACTIVE (ADMIN)
    await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    res_archived = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ARCHIVED"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_archived.status_code == status.HTTP_200_OK
    assert res_archived.json()["status"] == "ARCHIVED"

    res_reopen_arch_coord = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_reopen_arch_coord.status_code == status.HTTP_403_FORBIDDEN

    res_reopen_arch_admin = await classes_client.patch(
        f"/api/v1/classes/{cls_lifecycle.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_reopen_arch_admin.status_code == status.HTTP_200_OK
    assert res_reopen_arch_admin.json()["status"] == "ACTIVE"

    # PLANNING -> ARCHIVED e ACTIVE -> ARCHIVED
    res_plan_arch = await classes_client.patch(
        f"/api/v1/classes/{cls_planning_to_archive.id}/status",
        json={"status": "ARCHIVED"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_plan_arch.status_code == status.HTTP_200_OK
    assert res_plan_arch.json()["status"] == "ARCHIVED"

    res_act_arch = await classes_client.patch(
        f"/api/v1/classes/{cls_active_to_archive.id}/status",
        json={"status": "ARCHIVED"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_act_arch.status_code == status.HTTP_200_OK
    assert res_act_arch.json()["status"] == "ARCHIVED"

    # Transições inválidas a partir de ARCHIVED -> PLANNING ou COMPLETED
    for forbidden_target in ("PLANNING", "COMPLETED"):
        res_invalid_arch = await classes_client.patch(
            f"/api/v1/classes/{cls_active_to_archive.id}/status",
            json={"status": forbidden_target},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_invalid_arch.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert res_invalid_arch.json()["error"] == "INVALID_STATUS_TRANSITION"

    # 5. Bloqueio de ativação quando o curso vinculado foi desativado posteriormente
    with db_session_factory() as session:
        course_repo = CourseRepository(session=session)
        loaded_course = course_repo.get_by_id(course.id)
        assert loaded_course is not None
        course_repo.deactivate(loaded_course)

    cls_waiting_activation = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-4T",
        period="2026.4",
        status_value=ClassStatus.PLANNING,
    )
    res_inactive_course_act = await classes_client.patch(
        f"/api/v1/classes/{cls_waiting_activation.id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_inactive_course_act.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_inactive_course_act.json()["message"] == CLASS_ACTIVATION_INACTIVE_COURSE_MESSAGE

    # 6. 404, 400 UUID inválido e 400 payload inválido
    res_404 = await classes_client.patch(
        f"/api/v1/classes/{uuid4()}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == CLASS_NOT_FOUND_MESSAGE

    res_bad_uuid = await classes_client.patch(
        "/api/v1/classes/nao-eh-uuid/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_bad_uuid.status_code == status.HTTP_400_BAD_REQUEST

    res_bad_payload = await classes_client.patch(
        f"/api/v1/classes/{cls_waiting_activation.id}/status",
        json={"status": "ACTIVE", "extra": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_bad_payload.status_code == status.HTTP_400_BAD_REQUEST
