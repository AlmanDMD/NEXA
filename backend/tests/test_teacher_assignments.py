"""Testes unitários e de integração para Alocação de Docentes em Disciplinas e Turmas (BE-018)."""

from collections.abc import AsyncIterator, Generator
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    AcademicClass,
    Base,
    Course,
    Enrollment,
    LearningModule,
    Subject,
    TeacherAssignment,
    User,
)
from app.repositories.academic_class_repository import AcademicClassRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.course_repository import CourseRepository
from app.repositories.learning_module_repository import LearningModuleRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.enums import ClassStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.teacher_assignment_service import (
    TEACHER_ASSIGNMENT_CLASS_NOT_FOUND_MESSAGE,
    TEACHER_ASSIGNMENT_CONFLICT_MESSAGE,
    TEACHER_ASSIGNMENT_COURSE_MISMATCH_MESSAGE,
    TEACHER_ASSIGNMENT_INACTIVE_SUBJECT_MESSAGE,
    TEACHER_ASSIGNMENT_INACTIVE_TEACHER_MESSAGE,
    TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE,
    TEACHER_ASSIGNMENT_SUBJECT_NOT_FOUND_MESSAGE,
)


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[sa.Engine, None, None]:
    """Cria uma engine SQLite isolada por teste com modo WAL."""
    db_file = tmp_path / "teacher_assignments_test.db"
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
def assignments_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância FastAPI com dependências de banco e hasher sobrescritas."""
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
async def assignments_client(
    assignments_app: FastAPI,
) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=assignments_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_and_token(
    session_factory: sessionmaker[Session],
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
    full_name: str | None = None,
    registration_number: str | None = None,
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
                full_name=full_name or f"Usuário {role.value} {suffix}",
                registration_number=registration_number or f"SENAI-{role.value[:3]}-{suffix.upper()}",
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
) -> Course:
    """Persiste um curso técnico SENAI diretamente via repositório."""
    with session_factory() as session:
        repo = CourseRepository(session=session)
        return repo.create(
            code=code,
            name=name,
            description="Formação prática em usinagem, tornearia CNC e metrologia.",
            total_hours=1200,
            is_active=True,
        )


def _create_class_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "MEC-2026-1T",
    period: str = "2026.1",
    shift: Shift = Shift.MORNING,
) -> AcademicClass:
    """Persiste uma turma acadêmica diretamente via repositório."""
    with session_factory() as session:
        repo = AcademicClassRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            period=period,
            shift=shift,
            max_students=30,
            status=ClassStatus.ACTIVE,
            start_date=date(2026, 2, 2),
            end_date=date(2026, 6, 30),
        )


def _create_subject_in_db(
    session_factory: sessionmaker[Session],
    *,
    course_id: UUID,
    code: str = "USN-TOR-01",
    name: str = "Usinagem e Tornearia Mecânica",
    is_active: bool = True,
) -> Subject:
    """Persiste uma disciplina técnica diretamente via repositório."""
    with session_factory() as session:
        repo = SubjectRepository(session=session)
        return repo.create(
            course_id=course_id,
            code=code,
            name=name,
            workload_hours=120,
            syllabus="Torneamento cilíndrico, faceamento e segurança NR-12.",
            is_active=is_active,
        )


def test_teacher_assignment_orm_validations_and_db_constraints(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida regras ORM e chave única composta uq_teacher_assignments_composite."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject_usinagem = _create_subject_in_db(db_session_factory, course_id=course.id)
    subject_metrologia = _create_subject_in_db(
        db_session_factory,
        course_id=course.id,
        code="MET-DIM-01",
        name="Metrologia Dimensional",
    )

    teacher_1, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="orm1"
    )
    teacher_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="orm2"
    )

    with pytest.raises(ValueError, match="is_main_teacher"):
        TeacherAssignment(
            teacher_id=teacher_1.id,
            class_id=academic_class.id,
            subject_id=subject_usinagem.id,
            is_main_teacher="sim",  # type: ignore[arg-type]
        )

    valid_main = TeacherAssignment(
        teacher_id=teacher_1.id,
        class_id=academic_class.id,
        subject_id=subject_usinagem.id,
        is_main_teacher=True,
    )
    with db_session_factory() as session:
        session.add(valid_main)
        session.commit()

    # Mesmo docente, mesma turma e mesma disciplina viola uq_teacher_assignments_composite
    with db_session_factory() as session:
        duplicate = TeacherAssignment(
            teacher_id=teacher_1.id,
            class_id=academic_class.id,
            subject_id=subject_usinagem.id,
            is_main_teacher=False,
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    # Múltiplos docentes na mesma oficina/turma e o mesmo docente em outra disciplina são permitidos
    with db_session_factory() as session:
        co_teacher = TeacherAssignment(
            teacher_id=teacher_2.id,
            class_id=academic_class.id,
            subject_id=subject_usinagem.id,
            is_main_teacher=False,
        )
        other_subject = TeacherAssignment(
            teacher_id=teacher_1.id,
            class_id=academic_class.id,
            subject_id=subject_metrologia.id,
            is_main_teacher=True,
        )
        session.add_all([co_teacher, other_subject])
        session.commit()


async def test_teacher_assignments_rbac_allows_only_admin_and_coordinator(
    assignments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante RBAC: 401 sem token, 403 para STUDENT/TEACHER e 201 para COORDINATOR/ADMIN."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)

    teacher_1, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="rbac_t1"
    )
    teacher_2, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="rbac_t2"
    )
    _, student_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="rbac_stu"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="rbac_crd"
    )
    _, admin_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="rbac_adm"
    )

    payload_t1 = {
        "teacher_id": str(teacher_1.id),
        "class_id": str(academic_class.id),
        "subject_id": str(subject.id),
    }

    res_unauth = await assignments_client.post("/api/v1/teacher-assignments", json=payload_t1)
    assert res_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    for forbidden_token in (student_token, teacher_token):
        res_forbidden = await assignments_client.post(
            "/api/v1/teacher-assignments",
            json=payload_t1,
            headers={"Authorization": f"Bearer {forbidden_token}"},
        )
        assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN
        assert res_forbidden.json()["message"] == "Acesso não autorizado para seu perfil"

    res_coord = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json=payload_t1,
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_coord.status_code == status.HTTP_201_CREATED

    res_admin = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_2.id),
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "is_main_teacher": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == status.HTTP_201_CREATED


async def test_create_teacher_assignment_success_shared_workshop_and_conflict(
    assignments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios de Aceitação: 201 com múltiplos instrutores por oficina e 409 em duplicidade."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject_usinagem = _create_subject_in_db(db_session_factory, course_id=course.id)

    main_teacher, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="main",
        full_name="Prof. Roberto Tornearia",
        registration_number="SENAI-DOC-001",
    )
    workshop_instructor, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="aux",
        full_name="Instrutor Marcos Usinagem",
        registration_number="SENAI-DOC-002",
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="crd_ok"
    )

    # 1. Alocação do professor titular (is_main_teacher padrão True)
    res_main = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(main_teacher.id),
            "class_id": str(academic_class.id),
            "subject_id": str(subject_usinagem.id),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_main.status_code == status.HTTP_201_CREATED
    body_main = res_main.json()
    UUID(body_main["id"])
    assert body_main["teacher_id"] == str(main_teacher.id)
    assert body_main["class_id"] == str(academic_class.id)
    assert body_main["subject_id"] == str(subject_usinagem.id)
    assert body_main["is_main_teacher"] is True
    assert body_main["assigned_at"] is not None
    assert body_main["teacher"]["full_name"] == "Prof. Roberto Tornearia"
    assert body_main["teacher"]["registration_number"] == "SENAI-DOC-001"
    assert body_main["academic_class"]["code"] == "MEC-2026-1T"
    assert body_main["subject"]["code"] == "USN-TOR-01"

    # 2. Múltiplos docentes na mesma oficina (supervisão compartilhada com is_main_teacher=False)
    res_shared = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(workshop_instructor.id),
            "class_id": str(academic_class.id),
            "subject_id": str(subject_usinagem.id),
            "is_main_teacher": False,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_shared.status_code == status.HTTP_201_CREATED
    body_shared = res_shared.json()
    assert body_shared["is_main_teacher"] is False
    assert body_shared["teacher"]["full_name"] == "Instrutor Marcos Usinagem"

    # 3. Duplicidade do mesmo professor na mesma disciplina e turma retorna HTTP 409
    res_conflict = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(main_teacher.id),
            "class_id": str(academic_class.id),
            "subject_id": str(subject_usinagem.id),
            "is_main_teacher": False,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_conflict.status_code == status.HTTP_409_CONFLICT
    assert res_conflict.json()["message"] == TEACHER_ASSIGNMENT_CONFLICT_MESSAGE


async def test_create_teacher_assignment_validates_teacher_role_and_domain_rules(
    assignments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critérios de Aceitação: HTTP 400 se não for TEACHER cadastrado; 404/422 para turma e disciplina."""
    course_mec = _create_course_in_db(db_session_factory, code="TEC-MEC-01", name="Mecânica")
    course_ele = _create_course_in_db(
        db_session_factory, code="TEC-ELE-01", name="Eletrotécnica"
    )
    class_mec = _create_class_in_db(db_session_factory, course_id=course_mec.id)
    subject_mec_active = _create_subject_in_db(
        db_session_factory, course_id=course_mec.id, code="USN-01", name="Usinagem"
    )
    subject_mec_inactive = _create_subject_in_db(
        db_session_factory,
        course_id=course_mec.id,
        code="USN-OLD",
        name="Ajustagem Legada",
        is_active=False,
    )
    subject_ele = _create_subject_in_db(
        db_session_factory,
        course_id=course_ele.id,
        code="ELE-01",
        name="Instalações Elétricas",
    )

    teacher_active, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="val_t"
    )
    teacher_inactive, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="val_t_off",
        is_active=False,
    )
    student_user, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.STUDENT, suffix="val_stu"
    )
    coord_user, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="val_crd"
    )
    admin_user, _ = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.ADMIN, suffix="val_adm"
    )

    # Usuário inexistente, STUDENT, COORDINATOR ou ADMIN -> HTTP 400
    for invalid_teacher_id in (uuid4(), student_user.id, coord_user.id, admin_user.id):
        res_bad_teacher = await assignments_client.post(
            "/api/v1/teacher-assignments",
            json={
                "teacher_id": str(invalid_teacher_id),
                "class_id": str(class_mec.id),
                "subject_id": str(subject_mec_active.id),
            },
            headers={"Authorization": f"Bearer {coord_token}"},
        )
        assert res_bad_teacher.status_code == status.HTTP_400_BAD_REQUEST
        assert res_bad_teacher.json()["message"] == TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE

    # Professor com conta inativa -> HTTP 400
    res_inactive_teacher = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_inactive.id),
            "class_id": str(class_mec.id),
            "subject_id": str(subject_mec_active.id),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_teacher.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        res_inactive_teacher.json()["message"] == TEACHER_ASSIGNMENT_INACTIVE_TEACHER_MESSAGE
    )

    # Turma inexistente -> HTTP 404
    res_class_404 = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_active.id),
            "class_id": str(uuid4()),
            "subject_id": str(subject_mec_active.id),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_class_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_class_404.json()["message"] == TEACHER_ASSIGNMENT_CLASS_NOT_FOUND_MESSAGE

    # Disciplina inexistente -> HTTP 404
    res_subject_404 = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_active.id),
            "class_id": str(class_mec.id),
            "subject_id": str(uuid4()),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_subject_404.status_code == status.HTTP_404_NOT_FOUND
    assert res_subject_404.json()["message"] == TEACHER_ASSIGNMENT_SUBJECT_NOT_FOUND_MESSAGE

    # Disciplina inativa -> HTTP 422
    res_inactive_subject = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_active.id),
            "class_id": str(class_mec.id),
            "subject_id": str(subject_mec_inactive.id),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_inactive_subject.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        res_inactive_subject.json()["message"] == TEACHER_ASSIGNMENT_INACTIVE_SUBJECT_MESSAGE
    )

    # Disciplina de outro curso -> HTTP 422
    res_course_mismatch = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_active.id),
            "class_id": str(class_mec.id),
            "subject_id": str(subject_ele.id),
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_course_mismatch.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert (
        res_course_mismatch.json()["message"] == TEACHER_ASSIGNMENT_COURSE_MISMATCH_MESSAGE
    )

    # Schema estrito rejeita boolean inválido e campo extra -> HTTP 400
    res_bad_bool = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher_active.id),
            "class_id": str(class_mec.id),
            "subject_id": str(subject_mec_active.id),
            "is_main_teacher": "true",
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_bad_bool.status_code == status.HTTP_400_BAD_REQUEST


async def test_teacher_assignment_unlocks_contextual_class_and_module_access(
    assignments_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Integração end-to-end: após alocação via POST, docente acessa pauta da turma e módulos."""
    course = _create_course_in_db(db_session_factory)
    academic_class = _create_class_in_db(db_session_factory, course_id=course.id)
    subject = _create_subject_in_db(db_session_factory, course_id=course.id)

    with db_session_factory() as session:
        module_repo = LearningModuleRepository(session=session)
        module_repo.create(
            subject_id=subject.id,
            title="Torneamento Cilíndrico Externo",
            order_index=1,
            practical_hours=40,
        )

    student, _ = _create_user_and_token(
        db_session_factory,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="e2e_stu",
        full_name="João Pedro Usinagem",
        registration_number="SENAI-2026-E2E",
    )
    with db_session_factory() as session:
        session.add(Enrollment(student_id=student.id, class_id=academic_class.id))
        session.commit()

    teacher, teacher_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.TEACHER, suffix="e2e_tch"
    )
    _, coord_token = _create_user_and_token(
        db_session_factory, fast_hasher, role=UserRole.COORDINATOR, suffix="e2e_crd"
    )

    # Antes da alocação: acesso bloqueado (403) tanto na pauta da turma quanto nos módulos
    assert (
        await assignments_client.get(
            f"/api/v1/classes/{academic_class.id}/students",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
    ).status_code == status.HTTP_403_FORBIDDEN
    assert (
        await assignments_client.get(
            f"/api/v1/subjects/{subject.id}/modules",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
    ).status_code == status.HTTP_403_FORBIDDEN

    # Coordenador aloca docente via endpoint BE-018
    res_assign = await assignments_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(teacher.id),
            "class_id": str(academic_class.id),
            "subject_id": str(subject.id),
            "is_main_teacher": True,
        },
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_assign.status_code == status.HTTP_201_CREATED

    # Após a alocação: docente passa a visualizar pauta da turma e módulos práticos (200)
    res_students = await assignments_client.get(
        f"/api/v1/classes/{academic_class.id}/students",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_students.status_code == status.HTTP_200_OK
    assert res_students.json()["total"] == 1
    assert res_students.json()["data"][0]["full_name"] == "João Pedro Usinagem"

    res_modules = await assignments_client.get(
        f"/api/v1/subjects/{subject.id}/modules",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_modules.status_code == status.HTTP_200_OK
    assert res_modules.json()["total"] == 1
