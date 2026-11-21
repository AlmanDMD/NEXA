"""Testes unitários, de integração e de concorrência para Matrículas de Estudantes em Turmas (BE-016)."""

import asyncio
from collections.abc import AsyncIterator, Generator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import AcademicClass, AuditLog, Base, Course, Enrollment, User
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.schemas.enums import ClassStatus, EnrollmentStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.audit_service import AuditService
from app.services.enrollment_service import (
    ENROLLMENT_ALREADY_EXISTS_MESSAGE,
    ENROLLMENT_CLASS_FULL_MESSAGE,
    ENROLLMENT_CLASS_NOT_FOUND_MESSAGE,
    ENROLLMENT_INACTIVE_CLASS_MESSAGE,
    ENROLLMENT_INACTIVE_COURSE_MESSAGE,
    ENROLLMENT_INACTIVE_STUDENT_MESSAGE,
    ENROLLMENT_INVALID_STUDENT_ROLE_MESSAGE,
    ENROLLMENT_NOT_FOUND_MESSAGE,
    ENROLLMENT_REACTIVATION_INACTIVE_CLASS_MESSAGE,
    ENROLLMENT_STUDENT_NOT_FOUND_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com conexões independentes e modo WAL."""
    db_file = tmp_path / "enrollments_test.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
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
def enrollments_app(
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
async def enrollments_client(enrollments_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=enrollments_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
    is_active: bool = True,
) -> tuple[User, str]:
    """Cria um usuário persistido no banco de testes e gera seu Access Token JWT."""
    with session_factory() as session:
        repo = AuthRepository(session=session)
        user = repo.create_user(
            email=f"{role.value.lower()}.{suffix}@senai.br",
            password_hash=hasher.hash_password("Senai@2026!Secret"),
            role=role,
            is_active=is_active,
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
    is_active: bool = True,
) -> Course:
    """Helper para persistir um curso técnico SENAI diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description="Formação técnica em usinagem, tornearia e metrologia.",
            total_hours=1200,
            is_active=is_active,
        )


def _create_class_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "MEC-2026-1T",
    period: str = "2026.1",
    shift: Shift = Shift.MORNING,
    max_students: int = 40,
    status_value: ClassStatus = ClassStatus.ACTIVE,
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
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )


def test_enrollment_orm_validations_and_db_constraints(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida regras unitárias ORM e constraints relacionais (uq_enrollments_student_class e CHECKs)."""
    course = _create_course_in_db(db_session_factory)
    class_1 = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-1T")
    class_2 = _create_class_in_db(db_session_factory, course_id=course.id, code="MEC-2026-2T")
    student_1, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="orm1"
    )
    student_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="orm2"
    )

    valid_enrollment = Enrollment(
        student_id=student_1.id,
        class_id=class_1.id,
        enrollment_date=date(2026, 2, 2),
        status=EnrollmentStatus.ACTIVE,
        final_grade=Decimal("8.5"),
        attendance_rate=Decimal("95.0"),
    )
    assert valid_enrollment.final_grade == Decimal("8.50")
    assert valid_enrollment.attendance_rate == Decimal("95.00")

    with pytest.raises(ValueError, match="objeto date válido"):
        Enrollment(
            student_id=student_1.id,
            class_id=class_1.id,
            enrollment_date=datetime(2026, 2, 2, 8, 0),
        )

    for bad_grade in (Decimal("-0.01"), Decimal("10.01"), True):
        with pytest.raises(ValueError, match="final_grade"):
            Enrollment(
                student_id=student_1.id,
                class_id=class_1.id,
                final_grade=bad_grade,  # type: ignore[arg-type]
            )

    for bad_att in (Decimal("-0.01"), Decimal("100.01"), True):
        with pytest.raises(ValueError, match="attendance_rate"):
            Enrollment(
                student_id=student_1.id,
                class_id=class_1.id,
                attendance_rate=bad_att,  # type: ignore[arg-type]
            )

    # Persistência válida + UNIQUE (student_id, class_id)
    with db_session_factory() as session:
        session.add(valid_enrollment)
        session.commit()

    with db_session_factory() as session:
        duplicate_enrollment = Enrollment(
            student_id=student_1.id,
            class_id=class_1.id,
            status=EnrollmentStatus.ACTIVE,
        )
        session.add(duplicate_enrollment)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Mesmo estudante em outra turma deve ser permitido
    with db_session_factory() as session:
        other_class_enrollment = Enrollment(
            student_id=student_1.id,
            class_id=class_2.id,
        )
        session.add(other_class_enrollment)
        session.commit()

    # Constraints CHECK SQL diretas em final_grade e attendance_rate
    for bad_sql_row in (
        {"final_grade": -0.5, "attendance_rate": 80.0},
        {"final_grade": 10.5, "attendance_rate": 80.0},
        {"final_grade": 8.0, "attendance_rate": -1.0},
        {"final_grade": 8.0, "attendance_rate": 105.0},
    ):
        with db_session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    sa.text(
                        "INSERT INTO enrollments "
                        "(id, student_id, class_id, final_grade, attendance_rate) "
                        "VALUES (:id, :student_id, :class_id, :final_grade, :attendance_rate)"
                    ),
                    {
                        "id": str(uuid4()).replace("-", ""),
                        "student_id": str(student_2.id).replace("-", ""),
                        "class_id": str(class_1.id).replace("-", ""),
                        **bad_sql_row,
                    },
                )
                session.commit()
            session.rollback()


async def test_enrollments_rbac_blocks_unauthenticated_student_and_teacher(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante 401 sem autenticação, 403 para STUDENT/TEACHER e 201 para ADMIN/COORDINATOR."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id, max_students=10)

    student_1, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="rbac1"
    )
    student_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="rbac2"
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

    payload_1 = {"student_id": str(student_1.id), "class_id": str(academic_class.id)}

    unauth_res = await enrollments_client.post("/api/v1/enrollments", json=payload_1)
    assert unauth_res.status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_token in (student_token, teacher_token):
        forbidden_res = await enrollments_client.post(
            "/api/v1/enrollments",
            json=payload_1,
            headers={"Authorization": f"Bearer {forbidden_token}"},
        )
        assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN
        assert forbidden_res.json()["message"] == "Acesso não autorizado para seu perfil"

    coord_res = await enrollments_client.post(
        "/api/v1/enrollments",
        json=payload_1,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert coord_res.status_code == status.HTTP_201_CREATED

    admin_res = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_2.id), "class_id": str(academic_class.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == status.HTTP_201_CREATED


async def test_create_enrollment_success_and_updates_class_slots_integration(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios #1 e #2: POST /api/v1/enrollments retorna 201 e reflete nas vagas da turma (BE-012)."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        max_students=5,
        status_value=ClassStatus.ACTIVE,
    )
    student, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="ok1"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd"
    )

    response = await enrollments_client.post(
        "/api/v1/enrollments",
        json={
            "student_id": str(student.id),
            "class_id": str(academic_class.id),
            "enrollment_date": "2026-02-03",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    UUID(body["id"])
    assert body["student_id"] == str(student.id)
    assert body["class_id"] == str(academic_class.id)
    assert body["enrollment_date"] == "2026-02-03"
    assert body["status"] == EnrollmentStatus.ACTIVE.value
    assert body["final_grade"] is None
    assert body["attendance_rate"] is None
    assert body["student"]["id"] == str(student.id)
    assert body["student"]["role"] == UserRole.STUDENT.value
    assert body["student"]["full_name"] == "Usuário STUDENT ok1"
    assert body["student"]["registration_number"] == "SENAI-STU-OK1"
    assert body["academic_class"]["id"] == str(academic_class.id)
    assert body["academic_class"]["code"] == "MEC-2026-1T"
    assert body["academic_class"]["max_students"] == 5

    # Integração com BE-012: GET /api/v1/classes/{id} contabiliza a matrícula ativa
    class_res = await enrollments_client.get(
        f"/api/v1/classes/{academic_class.id}",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert class_res.status_code == status.HTTP_200_OK
    class_body = class_res.json()
    assert class_body["enrolled_students_count"] == 1
    assert class_body["available_slots"] == 4


async def test_create_enrollment_returns_409_when_student_already_enrolled(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério #3: HTTP 409 Conflict se aluno já estiver matriculado na turma (mesmo se turma lotar)."""
    course = _create_course_in_db(db_session_factory)
    class_1 = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-1T",
        max_students=1,
        status_value=ClassStatus.ACTIVE,
    )
    class_2 = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-2T",
        max_students=2,
        status_value=ClassStatus.ACTIVE,
    )
    student, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="dup"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="adm"
    )

    first_res = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student.id), "class_id": str(class_1.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert first_res.status_code == status.HTTP_201_CREATED

    # Segunda matrícula do mesmo aluno na mesma turma deve retornar 409 Conflict
    dup_res = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student.id), "class_id": str(class_1.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dup_res.status_code == status.HTTP_409_CONFLICT
    assert dup_res.json()["error"] == "CONFLICT"
    assert dup_res.json()["message"] == ENROLLMENT_ALREADY_EXISTS_MESSAGE

    # Mesmo estudante pode ser matriculado em outra turma ativa
    other_class_res = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student.id), "class_id": str(class_2.id)},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert other_class_res.status_code == status.HTTP_201_CREATED


async def test_create_enrollment_returns_422_when_class_full_and_ignores_non_active_enrollments(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério #4: HTTP 422 se max_students atingido; apenas matrículas ACTIVE consomem vaga."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-CAP",
        max_students=2,
        status_value=ClassStatus.ACTIVE,
    )
    s1, _ = _create_user_and_token(db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="c1")
    s2, _ = _create_user_and_token(db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="c2")
    s3, _ = _create_user_and_token(db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="c3")
    s4, _ = _create_user_and_token(db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="c4")
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd"
    )

    # Pré-registra uma matrícula DROPPED e uma COMPLETED que não devem consumir vagas ativas
    with db_session_factory() as session:
        session.add_all(
            [
                Enrollment(
                    student_id=s1.id,
                    class_id=academic_class.id,
                    status=EnrollmentStatus.DROPPED,
                ),
                Enrollment(
                    student_id=s2.id,
                    class_id=academic_class.id,
                    status=EnrollmentStatus.COMPLETED,
                ),
            ]
        )
        session.commit()

    # Ainda há 2 vagas ativas disponíveis (para s3 e s4)
    res_s3 = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(s3.id), "class_id": str(academic_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_s3.status_code == status.HTTP_201_CREATED

    res_s4 = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(s4.id), "class_id": str(academic_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_s4.status_code == status.HTTP_201_CREATED

    # 5º estudante tenta entrar com as 2 vagas ativas ocupadas -> HTTP 422
    s5, _ = _create_user_and_token(db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="c5")
    res_full = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(s5.id), "class_id": str(academic_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_full.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_full.json()["error"] == "UNPROCESSABLE_ENTITY"
    assert res_full.json()["message"] == ENROLLMENT_CLASS_FULL_MESSAGE


async def test_create_enrollment_validates_existence_roles_and_active_states(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida 404 para turma/aluno inexistentes, 422 para estados inválidos/role e 400 para payload."""
    active_course = _create_course_in_db(db_session_factory, code="TEC-MEC-01", is_active=True)
    inactive_course = _create_course_in_db(
        db_session_factory, code="TEC-OLD-01", name="Curso Inativo", is_active=False
    )

    active_class = _create_class_in_db(
        db_session_factory,
        course_id=active_course.id,
        code="MEC-ACT-01",
        status_value=ClassStatus.ACTIVE,
    )
    planning_class = _create_class_in_db(
        db_session_factory,
        course_id=active_course.id,
        code="MEC-PLN-01",
        status_value=ClassStatus.PLANNING,
    )
    completed_class = _create_class_in_db(
        db_session_factory,
        course_id=active_course.id,
        code="MEC-CMP-01",
        status_value=ClassStatus.COMPLETED,
    )
    archived_class = _create_class_in_db(
        db_session_factory,
        course_id=active_course.id,
        code="MEC-ARC-01",
        status_value=ClassStatus.ARCHIVED,
    )
    inactive_course_class = _create_class_in_db(
        db_session_factory,
        course_id=inactive_course.id,
        code="OLD-ACT-01",
        status_value=ClassStatus.ACTIVE,
    )

    active_student, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="act"
    )
    inactive_student, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="inact", is_active=False
    )
    teacher_user, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="t1"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="c1"
    )

    # 1. Turma inexistente -> 404
    res_no_class = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(active_student.id), "class_id": str(uuid4())},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_no_class.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_class.json()["message"] == ENROLLMENT_CLASS_NOT_FOUND_MESSAGE

    # 2. Estudante inexistente -> 404
    res_no_student = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(uuid4()), "class_id": str(active_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_no_student.status_code == status.HTTP_404_NOT_FOUND
    assert res_no_student.json()["message"] == ENROLLMENT_STUDENT_NOT_FOUND_MESSAGE

    # 3. Turmas não ativas (PLANNING, COMPLETED, ARCHIVED) -> 422
    for non_active_cls in (planning_class, completed_class, archived_class):
        res_cls = await enrollments_client.post(
            "/api/v1/enrollments",
            json={"student_id": str(active_student.id), "class_id": str(non_active_cls.id)},
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res_cls.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert res_cls.json()["message"] == ENROLLMENT_INACTIVE_CLASS_MESSAGE

    # 4. Turma cujo curso está inativo -> 422
    res_inactive_course = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(active_student.id), "class_id": str(inactive_course_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_course.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_inactive_course.json()["message"] == ENROLLMENT_INACTIVE_COURSE_MESSAGE

    # 5. Usuário sem role STUDENT -> 422
    res_wrong_role = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(teacher_user.id), "class_id": str(active_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_wrong_role.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_wrong_role.json()["message"] == ENROLLMENT_INVALID_STUDENT_ROLE_MESSAGE

    # 6. Estudante com is_active=False -> 422
    res_inactive_student = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(inactive_student.id), "class_id": str(active_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_student.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_inactive_student.json()["message"] == ENROLLMENT_INACTIVE_STUDENT_MESSAGE

    # 7. Payloads malformados / campos extras -> 400
    invalid_payloads: list[dict[str, Any]] = [
        {"student_id": "not-uuid", "class_id": str(active_class.id)},
        {"student_id": str(active_student.id), "class_id": "not-uuid"},
        {
            "student_id": str(active_student.id),
            "class_id": str(active_class.id),
            "enrollment_date": "02/02/2026",
        },
        {
            "student_id": str(active_student.id),
            "class_id": str(active_class.id),
            "extra_field": True,
        },
    ]
    for bad_payload in invalid_payloads:
        bad_res = await enrollments_client.post(
            "/api/v1/enrollments",
            json=bad_payload,
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert bad_res.status_code == status.HTTP_400_BAD_REQUEST
        assert bad_res.json()["error"] == "VALIDATION_ERROR"


async def test_concurrent_enrollments_prevent_overbooking_and_duplicate_race_conditions(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """DoD & Observação Técnica: Valida atomicidade sob chamadas simultâneas (zero overbooking e zero duplicidade)."""
    course = _create_course_in_db(db_session_factory)
    class_limited = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-CONC-01",
        max_students=3,
        status_value=ClassStatus.ACTIVE,
    )
    class_dup_race = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-CONC-02",
        max_students=10,
        status_value=ClassStatus.ACTIVE,
    )

    students = [
        _create_user_and_token(
            db_session_factory,
            fast_hasher,
            role=UserRole.STUDENT,
            suffix=f"conc{idx}",
        )[0]
        for idx in range(8)
    ]
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="concadm"
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. 8 estudantes disputando simultaneamente 3 vagas na mesma turma
    overbooking_responses = await asyncio.gather(
        *[
            enrollments_client.post(
                "/api/v1/enrollments",
                json={"student_id": str(stu.id), "class_id": str(class_limited.id)},
                headers=headers,
            )
            for stu in students
        ]
    )
    status_codes = [res.status_code for res in overbooking_responses]
    assert status_codes.count(status.HTTP_201_CREATED) == 3
    assert status_codes.count(status.HTTP_422_UNPROCESSABLE_CONTENT) == 5
    assert all(
        res.json()["message"] == ENROLLMENT_CLASS_FULL_MESSAGE
        for res in overbooking_responses
        if res.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    )

    with db_session_factory() as session:
        persisted_count = int(
            session.scalar(
                select(func.count())
                .select_from(Enrollment)
                .where(Enrollment.class_id == class_limited.id)
            )
            or 0
        )
        assert persisted_count == 3

    # 2. Mesmo estudante disparando 5 requisições simultâneas para a mesma turma com vagas
    target_student = students[0]
    duplicate_race_responses = await asyncio.gather(
        *[
            enrollments_client.post(
                "/api/v1/enrollments",
                json={"student_id": str(target_student.id), "class_id": str(class_dup_race.id)},
                headers=headers,
            )
            for _ in range(5)
        ]
    )
    dup_codes = [res.status_code for res in duplicate_race_responses]
    assert dup_codes.count(status.HTTP_201_CREATED) == 1
    assert dup_codes.count(status.HTTP_409_CONFLICT) == 4
    assert all(
        res.json()["message"] == ENROLLMENT_ALREADY_EXISTS_MESSAGE
        for res in duplicate_race_responses
        if res.status_code == status.HTTP_409_CONFLICT
    )

    with db_session_factory() as session:
        dup_persisted_count = int(
            session.scalar(
                select(func.count())
                .select_from(Enrollment)
                .where(
                    Enrollment.class_id == class_dup_race.id,
                    Enrollment.student_id == target_student.id,
                )
            )
            or 0
        )
        assert dup_persisted_count == 1


def test_audit_log_orm_validations_and_audit_service(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida regras ORM de AuditLog (DB-009) e serialização JSON do AuditService."""
    actor, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="aud_adm"
    )

    for bad_action in ("", " ", "A"):
        with pytest.raises(ValueError, match="action"):
            AuditLog(action=bad_action, entity="enrollments", entity_id="123")

    for bad_entity in ("", "X"):
        with pytest.raises(ValueError, match="entity"):
            AuditLog(action="ENROLLMENT_STATUS_UPDATED", entity=bad_entity, entity_id="123")

    with pytest.raises(ValueError, match="entity_id"):
        AuditLog(action="ENROLLMENT_STATUS_UPDATED", entity="enrollments", entity_id="   ")

    target_id = uuid4()
    with db_session_factory() as session:
        service = AuditService(repository=AuditRepository(session=session))
        entry = service.log_action(
            user_id=actor.id,
            action="ENROLLMENT_STATUS_UPDATED",
            entity="enrollments",
            entity_id=target_id,
            old_values={"status": EnrollmentStatus.ACTIVE, "grade": Decimal("7.50")},
            new_values={"status": EnrollmentStatus.COMPLETED, "grade": Decimal("8.75")},
            ip_address="127.0.0.1",
            commit=True,
        )
        assert entry.id is not None
        assert entry.user_id == actor.id
        assert entry.entity_id == str(target_id)
        assert entry.old_values == {"status": "ACTIVE", "grade": 7.5} or entry.old_values == {
            "status": "ACTIVE",
            "grade": "7.50",
        }
        assert entry.new_values["status"] == "COMPLETED"
        assert entry.ip_address == "127.0.0.1"


async def test_update_enrollment_status_creates_audit_log_and_updates_active_metrics(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios BE-019: HTTP 200, audit_logs com old/new JSON e DROPPED fora das métricas ativas."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(
        db_session_factory,
        course_id=course.id,
        code="MEC-2026-ST",
        max_students=2,
        status_value=ClassStatus.ACTIVE,
    )
    stu_1, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="st1"
    )
    stu_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="st2"
    )
    stu_3, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="st3"
    )
    coordinator, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="st_crd"
    )
    headers = {"Authorization": f"Bearer {coord_token}"}

    res_enr_1 = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(stu_1.id), "class_id": str(academic_class.id)},
        headers=headers,
    )
    res_enr_2 = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(stu_2.id), "class_id": str(academic_class.id)},
        headers=headers,
    )
    assert res_enr_1.status_code == status.HTTP_201_CREATED
    assert res_enr_2.status_code == status.HTTP_201_CREATED
    enr_1_id = res_enr_1.json()["id"]
    enr_2_id = res_enr_2.json()["id"]

    # 1. Trancamento (DROPPED) com justificativa via PATCH /api/v1/enrollments/{id}/status
    res_drop = await enrollments_client.patch(
        f"/api/v1/enrollments/{enr_1_id}/status",
        json={
            "status": "DROPPED",
            "justification": "  Trancamento   formal   protocolado na secretaria.  ",
        },
        headers=headers,
    )
    assert res_drop.status_code == status.HTTP_200_OK
    drop_body = res_drop.json()
    assert drop_body["id"] == enr_1_id
    assert drop_body["status"] == "DROPPED"

    # Verifica registro gerado em audit_logs com old_values e new_values em JSON
    with db_session_factory() as session:
        logs = list(
            session.scalars(
                select(AuditLog)
                .where(
                    AuditLog.entity == "enrollments",
                    AuditLog.entity_id == enr_1_id,
                )
                .order_by(AuditLog.created_at.asc())
            ).all()
        )
        assert len(logs) == 1
        audit = logs[0]
        assert audit.user_id == coordinator.id
        assert audit.action == "ENROLLMENT_STATUS_UPDATED"
        assert audit.old_values == {
            "status": "ACTIVE",
            "student_id": str(stu_1.id),
            "class_id": str(academic_class.id),
        }
        assert audit.new_values == {
            "status": "DROPPED",
            "student_id": str(stu_1.id),
            "class_id": str(academic_class.id),
            "justification": "Trancamento formal protocolado na secretaria.",
        }

        # Alunos DROPPED deixam de integrar a lista elegível para chamada e cálculos de faltas futuras
        eligible = EnrollmentRepository(session=session).list_eligible_for_attendance(
            academic_class.id
        )
        assert [item.student_id for item in eligible] == [stu_2.id]

    # Métricas da turma refletem apenas alunos ativos (1 ativo, 1 vaga liberada)
    res_class = await enrollments_client.get(
        f"/api/v1/classes/{academic_class.id}",
        headers=headers,
    )
    assert res_class.status_code == status.HTTP_200_OK
    assert res_class.json()["enrolled_students_count"] == 1
    assert res_class.json()["available_slots"] == 1

    # Nova matrícula na vaga liberada ocupa novamente o limite max_students=2
    res_enr_3 = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(stu_3.id), "class_id": str(academic_class.id)},
        headers=headers,
    )
    assert res_enr_3.status_code == status.HTTP_201_CREATED

    # Tentar reativar aluno DROPPED para turma já lotada retorna HTTP 422
    res_reactivate_full = await enrollments_client.patch(
        f"/api/v1/enrollments/{enr_1_id}/status",
        json={"status": "ACTIVE", "justification": "Tentativa de retorno sem vaga."},
        headers=headers,
    )
    assert res_reactivate_full.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_reactivate_full.json()["message"] == ENROLLMENT_CLASS_FULL_MESSAGE

    # Transições para SUSPENDED e COMPLETED também registram auditoria
    res_suspend = await enrollments_client.patch(
        f"/api/v1/enrollments/{enr_2_id}/status",
        json={"status": "SUSPENDED"},
        headers=headers,
    )
    assert res_suspend.status_code == status.HTTP_200_OK
    assert res_suspend.json()["status"] == "SUSPENDED"

    res_complete = await enrollments_client.patch(
        f"/api/v1/enrollments/{res_enr_3.json()['id']}/status",
        json={"status": "COMPLETED", "justification": "Aproveitamento integral concluído."},
        headers=headers,
    )
    assert res_complete.status_code == status.HTTP_200_OK
    assert res_complete.json()["status"] == "COMPLETED"


async def test_update_enrollment_status_rbac_and_error_cases(
    enrollments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante RBAC (401/403 apenas ADMIN/COORDINATOR) e validação de erros (400/404/422)."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(
        db_session_factory, course_id=course.id, code="MEC-2026-RB", status_value=ClassStatus.ACTIVE
    )
    student, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="rbs"
    )
    _, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="rbt"
    )
    admin, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="rba"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="rbc"
    )

    res_create = await enrollments_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student.id), "class_id": str(academic_class.id)},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    enrollment_id = res_create.json()["id"]

    # Sem token -> 401
    res_unauth = await enrollments_client.patch(
        f"/api/v1/enrollments/{enrollment_id}/status",
        json={"status": "DROPPED"},
    )
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # STUDENT e TEACHER -> 403
    for forbidden_token in (student_token, teacher_token):
        res_forbidden = await enrollments_client.patch(
            f"/api/v1/enrollments/{enrollment_id}/status",
            json={"status": "DROPPED"},
            headers={"Authorization": f"Bearer {forbidden_token}"},
        )
        assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert res_forbidden.json()["message"] == "Acesso não autorizado para seu perfil"

    # Matrícula inexistente -> 404
    res_404 = await enrollments_client.patch(
        f"/api/v1/enrollments/{uuid4()}/status",
        json={"status": "DROPPED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_404.json()["message"] == ENROLLMENT_NOT_FOUND_MESSAGE

    # UUID inválido, status inválido, XSS/HTML na justificativa e campo extra -> 400
    assert (
        await enrollments_client.patch(
            "/api/v1/enrollments/id-invalido/status",
            json={"status": "DROPPED"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).status_code == status.HTTP_400_BAD_REQUEST

    assert (
        await enrollments_client.patch(
            f"/api/v1/enrollments/{enrollment_id}/status",
            json={"status": "CANCELADO"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).status_code == status.HTTP_400_BAD_REQUEST

    assert (
        await enrollments_client.patch(
            f"/api/v1/enrollments/{enrollment_id}/status",
            json={"status": "DROPPED", "justification": "<script>alert(1)</script>"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).status_code == status.HTTP_400_BAD_REQUEST

    assert (
        await enrollments_client.patch(
            f"/api/v1/enrollments/{enrollment_id}/status",
            json={"status": "DROPPED", "unexpected": "value"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).status_code == status.HTTP_400_BAD_REQUEST

    # ADMIN consegue atualizar status (200) e reativar se turma está ativa e há vaga
    res_admin_drop = await enrollments_client.patch(
        f"/api/v1/enrollments/{enrollment_id}/status",
        json={"status": "DROPPED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_drop.status_code == status.HTTP_200_OK

    # Arquiva a turma e valida bloqueio de reativação de matrícula (422)
    with db_session_factory() as session:
        cls_obj = session.get(AcademicClass, academic_class.id)
        assert cls_obj is not None
        cls_obj.status = ClassStatus.ARCHIVED
        session.commit()

    res_reactivate_archived = await enrollments_client.patch(
        f"/api/v1/enrollments/{enrollment_id}/status",
        json={"status": "ACTIVE"},
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_reactivate_archived.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        res_reactivate_archived.json()["message"]
        == ENROLLMENT_REACTIVATION_INACTIVE_CLASS_MESSAGE
    )

    with db_session_factory() as session:
        audits = list(
            session.scalars(
                select(AuditLog).where(
                    AuditLog.entity_id == enrollment_id,
                    AuditLog.user_id == admin.id,
                )
            ).all()
        )
        assert len(audits) == 1

