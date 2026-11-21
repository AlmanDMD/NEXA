"""Suíte de testes de integração da camada de Gestão Acadêmica SENAI (BE-020).

Executa contra banco de dados de testes isolado utilizando fixture assíncrona com
transação aninhada (SAVEPOINT) e rollback automático após cada teste, validando
todos os fluxos integrados de cursos, turmas, disciplinas, módulos práticos,
competências, matrículas, pauta de alunos, alocação docente e auditoria.
"""

from collections.abc import AsyncIterator, Generator
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
)
from app.main import create_app
from app.models import (
    AcademicClass,
    AuditLog,
    Base,
    Competency,
    Course,
    Enrollment,
    LearningModule,
    Subject,
    TeacherAssignment,
    User,
)
from app.repositories.auth_repository import AuthRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.schemas.enums import ClassStatus, CompetencyCategory, EnrollmentStatus, Shift, UserRole
from app.schemas.user import UserProfileCreateSchema
from app.services.academic_class_service import CLASS_TEACHER_FORBIDDEN_MESSAGE
from app.services.course_service import COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE
from app.services.enrollment_service import (
    ENROLLMENT_ALREADY_EXISTS_MESSAGE,
    ENROLLMENT_CLASS_FULL_MESSAGE,
)
from app.services.teacher_assignment_service import (
    TEACHER_ASSIGNMENT_CONFLICT_MESSAGE,
    TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE,
)


@pytest.fixture(scope="module")
def academic_engine() -> Generator[sa.Engine, None, None]:
    """Cria o schema completo SQLAlchemy 2.0 uma única vez por módulo em banco isolado."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Workaround oficial SQLAlchemy 2.0 para SAVEPOINT confiável com sqlite3/pysqlite
    @event.listens_for(engine, "connect")
    def _do_connect(dbapi_connection: Any, _connection_record: Any) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _do_begin(conn: sa.Connection) -> None:
        conn.exec_driver_sql("BEGIN")

    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="module")
def fast_hasher() -> PasswordHasher:
    """Instância rápida do PasswordHasher (rounds=4) para criação ágil de usuários em testes."""
    return PasswordHasher(rounds=4)


@pytest.fixture
async def db_session(academic_engine: sa.Engine) -> AsyncIterator[Session]:
    """Fixture assíncrona com transação aninhada (SAVEPOINT) e rollback automático pós-teste."""
    connection = academic_engine.connect()
    outer_transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        if outer_transaction.is_active:
            outer_transaction.rollback()
        connection.close()


@pytest.fixture
async def academic_app(
    db_session: Session,
    fast_hasher: PasswordHasher,
) -> AsyncIterator[FastAPI]:
    """Instância FastAPI integrada com a sessão transacional isolada por teste."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture
async def async_client(academic_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono (httpx.AsyncClient) acoplado à aplicação FastAPI."""
    transport = ASGITransport(app=academic_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user_with_token(
    session: Session,
    hasher: PasswordHasher,
    *,
    role: UserRole,
    suffix: str,
    full_name: str,
    registration_number: str,
    is_active: bool = True,
) -> tuple[User, dict[str, str]]:
    """Persiste usuário na transação aninhada atual e retorna entidade + header Bearer."""
    repo = AuthRepository(session=session)
    user = repo.create_user(
        email=f"{role.value.lower()}.{suffix}@senai.nexa.local",
        password_hash=hasher.hash_password("Senai@2026!Secret"),
        role=role,
        is_active=is_active,
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
    return user, {"Authorization": f"Bearer {token}"}


async def test_full_senai_academic_curriculum_lifecycle_e2e(
    async_client: AsyncClient,
    db_session: Session,
    fast_hasher: PasswordHasher,
) -> None:
    """Valida criação, consulta e atualização de Curso, Turma, Disciplina, Módulos e Competências."""
    _, coord_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="e2e_coord",
        full_name="Coordenador Pedagógico SENAI",
        registration_number="SENAI-CRD-001",
    )

    # 1. Curso Técnico SENAI (BE-011): POST -> GET detail -> GET list -> PUT
    res_course = await async_client.post(
        "/api/v1/courses",
        json={
            "code": "TEC-MEC-01",
            "name": "Técnico em Mecânica Industrial",
            "description": "Formação em metrologia e processos de usinagem.",
            "total_hours": 1200,
        },
        headers=coord_headers,
    )
    assert res_course.status_code == status.HTTP_201_CREATED
    course_id = res_course.json()["id"]

    res_course_get = await async_client.get(
        f"/api/v1/courses/{course_id}",
        headers=coord_headers,
    )
    assert res_course_get.status_code == status.HTTP_200_OK
    assert res_course_get.json()["code"] == "TEC-MEC-01"

    res_course_list = await async_client.get(
        "/api/v1/courses?search=Mecânica&is_active=true",
        headers=coord_headers,
    )
    assert res_course_list.status_code == status.HTTP_200_OK
    assert res_course_list.json()["total"] == 1

    res_course_put = await async_client.put(
        f"/api/v1/courses/{course_id}",
        json={"total_hours": 1280},
        headers=coord_headers,
    )
    assert res_course_put.status_code == status.HTTP_200_OK
    assert res_course_put.json()["total_hours"] == 1280

    # 2. Turma Acadêmica SENAI (BE-012): POST (PLANNING) -> PATCH ACTIVE -> GET list/detail
    res_class = await async_client.post(
        "/api/v1/classes",
        json={
            "course_id": course_id,
            "code": "MEC-2026-1",
            "period": "2026.1",
            "shift": Shift.MORNING.value,
            "max_students": 30,
            "status": ClassStatus.PLANNING.value,
            "start_date": "2026-02-09",
            "end_date": "2026-07-10",
        },
        headers=coord_headers,
    )
    assert res_class.status_code == status.HTTP_201_CREATED
    class_id = res_class.json()["id"]

    res_class_activate = await async_client.patch(
        f"/api/v1/classes/{class_id}/status",
        json={"status": ClassStatus.ACTIVE.value},
        headers=coord_headers,
    )
    assert res_class_activate.status_code == status.HTTP_200_OK
    assert res_class_activate.json()["status"] == "ACTIVE"

    res_class_list = await async_client.get(
        f"/api/v1/classes?course_id={course_id}&period=2026.1&status=ACTIVE",
        headers=coord_headers,
    )
    assert res_class_list.status_code == status.HTTP_200_OK
    assert res_class_list.json()["total"] == 1

    # 3. Disciplinas Técnicas (BE-013): POST (Metrologia + Usinagem) -> GET -> PUT -> List
    res_sub_met = await async_client.post(
        "/api/v1/subjects",
        json={
            "course_id": course_id,
            "code": "UC-MET-01",
            "name": "Metrologia Dimensional",
            "workload_hours": 80,
            "syllabus": "Paquímetro, micrômetro e relógio comparador.",
        },
        headers=coord_headers,
    )
    res_sub_usi = await async_client.post(
        "/api/v1/subjects",
        json={
            "course_id": course_id,
            "code": "UC-USI-03",
            "name": "Usinagem Convencional",
            "workload_hours": 160,
            "syllabus": "Torneamento cilíndrico, faceamento e segurança NR-12.",
        },
        headers=coord_headers,
    )
    assert res_sub_met.status_code == status.HTTP_201_CREATED
    assert res_sub_usi.status_code == status.HTTP_201_CREATED
    sub_met_id = res_sub_met.json()["id"]

    res_sub_get = await async_client.get(
        f"/api/v1/subjects/{sub_met_id}",
        headers=coord_headers,
    )
    assert res_sub_get.status_code == status.HTTP_200_OK

    res_sub_put = await async_client.put(
        f"/api/v1/subjects/{sub_met_id}",
        json={"workload_hours": 100},
        headers=coord_headers,
    )
    assert res_sub_put.status_code == status.HTTP_200_OK
    assert res_sub_put.json()["workload_hours"] == 100

    res_sub_list = await async_client.get(
        f"/api/v1/subjects?course_id={course_id}&is_active=true",
        headers=coord_headers,
    )
    assert res_sub_list.status_code == status.HTTP_200_OK
    assert res_sub_list.json()["total"] == 2

    # 4. Módulos de Aprendizagem Prática (BE-014): ordem didática ascendente
    res_mod_2 = await async_client.post(
        "/api/v1/modules",
        json={
            "subject_id": sub_met_id,
            "title": "Metrologia com Micrômetro Centesimal",
            "order_index": 2,
            "practical_hours": 24,
            "passing_score": "7.00",
        },
        headers=coord_headers,
    )
    res_mod_1 = await async_client.post(
        "/api/v1/modules",
        json={
            "subject_id": sub_met_id,
            "title": "Metrologia com Paquímetro Universal",
            "order_index": 1,
            "practical_hours": 20,
            "passing_score": "6.50",
        },
        headers=coord_headers,
    )
    assert res_mod_2.status_code == status.HTTP_201_CREATED
    assert res_mod_1.status_code == status.HTTP_201_CREATED
    mod_1_id = res_mod_1.json()["id"]

    res_mod_list = await async_client.get(
        f"/api/v1/subjects/{sub_met_id}/modules",
        headers=coord_headers,
    )
    assert res_mod_list.status_code == status.HTTP_200_OK
    assert [m["order_index"] for m in res_mod_list.json()["data"]] == [1, 2]

    # 5. Competências Técnicas e Vínculo com Módulo (BE-015)
    res_comp_tech = await async_client.post(
        "/api/v1/competencies",
        json={
            "code": "COMP-MET-01",
            "title": "Leitura em Paquímetro Vernier 0,02mm",
            "category": CompetencyCategory.TECHNICAL.value,
        },
        headers=coord_headers,
    )
    res_comp_safe = await async_client.post(
        "/api/v1/competencies",
        json={
            "code": "COMP-SEG-01",
            "title": "Inspeção de EPIs e Segurança NR-12",
            "category": CompetencyCategory.SAFETY.value,
        },
        headers=coord_headers,
    )
    assert res_comp_tech.status_code == status.HTTP_201_CREATED
    assert res_comp_safe.status_code == status.HTTP_201_CREATED

    res_comp_list = await async_client.get(
        "/api/v1/competencies?category=TECHNICAL&search=Paquímetro",
        headers=coord_headers,
    )
    assert res_comp_list.status_code == status.HTTP_200_OK
    assert res_comp_list.json()["total"] == 1

    res_link = await async_client.post(
        f"/api/v1/modules/{mod_1_id}/competencies",
        json={
            "competency_id": res_comp_tech.json()["id"],
            "weight": "1.50",
            "required_level": 4,
        },
        headers=coord_headers,
    )
    assert res_link.status_code == status.HTTP_201_CREATED

    res_mod_comps = await async_client.get(
        f"/api/v1/modules/{mod_1_id}/competencies",
        headers=coord_headers,
    )
    assert res_mod_comps.status_code == status.HTTP_200_OK
    assert res_mod_comps.json()["total_competencies"] == 1
    assert res_mod_comps.json()["total_weight"] == "1.50"
    assert res_mod_comps.json()["categories_summary"]["TECHNICAL"] == 1


async def test_teacher_assignment_shared_workshop_and_contextual_rbac_flow(
    async_client: AsyncClient,
    db_session: Session,
    fast_hasher: PasswordHasher,
) -> None:
    """Valida alocação de múltiplos docentes na oficina (BE-018) e liberação de RBAC contextual."""
    _, admin_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="tch_adm",
        full_name="Administrador NEXA",
        registration_number="SENAI-ADM-001",
    )
    main_teacher, main_teacher_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tch_main",
        full_name="Prof. Roberto Tornearia",
        registration_number="SENAI-DOC-010",
    )
    workshop_teacher, workshop_teacher_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tch_aux",
        full_name="Instrutor Marcos Oficina",
        registration_number="SENAI-DOC-011",
    )
    _, unallocated_teacher_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="tch_other",
        full_name="Prof. Não Alocado",
        registration_number="SENAI-DOC-012",
    )
    student_user, _ = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="tch_stu",
        full_name="Lucas Ferreira",
        registration_number="SENAI-ALU-010",
    )

    course_id = (
        await async_client.post(
            "/api/v1/courses",
            json={"code": "TEC-USI-01", "name": "Técnico em Usinagem", "total_hours": 1000},
            headers=admin_headers,
        )
    ).json()["id"]
    class_id = (
        await async_client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "code": "USI-2026-1",
                "period": "2026.1",
                "shift": "AFTERNOON",
                "status": "ACTIVE",
                "start_date": "2026-02-09",
                "end_date": "2026-07-10",
            },
            headers=admin_headers,
        )
    ).json()["id"]
    subject_id = (
        await async_client.post(
            "/api/v1/subjects",
            json={
                "course_id": course_id,
                "code": "UC-TOR-01",
                "name": "Tornearia CNC",
                "workload_hours": 120,
            },
            headers=admin_headers,
        )
    ).json()["id"]

    # Usuário não docente -> HTTP 400
    res_bad_role = await async_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(student_user.id),
            "class_id": class_id,
            "subject_id": subject_id,
        },
        headers=admin_headers,
    )
    assert res_bad_role.status_code == status.HTTP_400_BAD_REQUEST
    assert res_bad_role.json()["message"] == TEACHER_ASSIGNMENT_INVALID_TEACHER_MESSAGE

    # Aloca professor titular e instrutor de oficina compartilhada -> HTTP 201
    res_assign_1 = await async_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(main_teacher.id),
            "class_id": class_id,
            "subject_id": subject_id,
            "is_main_teacher": True,
        },
        headers=admin_headers,
    )
    res_assign_2 = await async_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(workshop_teacher.id),
            "class_id": class_id,
            "subject_id": subject_id,
            "is_main_teacher": False,
        },
        headers=admin_headers,
    )
    assert res_assign_1.status_code == status.HTTP_201_CREATED
    assert res_assign_2.status_code == status.HTTP_201_CREATED
    assert res_assign_2.json()["is_main_teacher"] is False

    # Duplicidade do mesmo professor na mesma turma/disciplina -> HTTP 409
    res_dup = await async_client.post(
        "/api/v1/teacher-assignments",
        json={
            "teacher_id": str(main_teacher.id),
            "class_id": class_id,
            "subject_id": subject_id,
        },
        headers=admin_headers,
    )
    assert res_dup.status_code == status.HTTP_409_CONFLICT
    assert res_dup.json()["message"] == TEACHER_ASSIGNMENT_CONFLICT_MESSAGE

    # RBAC contextual: ambos docentes alocados acessam turma, pauta e criam módulos práticos
    for teacher_headers in (main_teacher_headers, workshop_teacher_headers):
        assert (
            await async_client.get(f"/api/v1/classes/{class_id}", headers=teacher_headers)
        ).status_code == status.HTTP_200_OK
        assert (
            await async_client.get(
                f"/api/v1/classes/{class_id}/students", headers=teacher_headers
            )
        ).status_code == status.HTTP_200_OK

    res_teacher_mod = await async_client.post(
        "/api/v1/modules",
        json={
            "subject_id": subject_id,
            "title": "Programação de Torno CNC Eixo X/Z",
            "practical_hours": 36,
            "passing_score": "7.50",
        },
        headers=workshop_teacher_headers,
    )
    assert res_teacher_mod.status_code == status.HTTP_201_CREATED

    # Professor NÃO alocado é bloqueado com HTTP 403
    res_denied_class = await async_client.get(
        f"/api/v1/classes/{class_id}/students",
        headers=unallocated_teacher_headers,
    )
    assert res_denied_class.status_code == status.HTTP_403_FORBIDDEN
    assert res_denied_class.json()["message"] == CLASS_TEACHER_FORBIDDEN_MESSAGE

    res_denied_modules = await async_client.get(
        f"/api/v1/subjects/{subject_id}/modules",
        headers=unallocated_teacher_headers,
    )
    assert res_denied_modules.status_code == status.HTTP_403_FORBIDDEN


async def test_student_enrollment_capacity_validation_roster_and_status_audit_flow(
    async_client: AsyncClient,
    db_session: Session,
    fast_hasher: PasswordHasher,
) -> None:
    """Valida matrícula atômica com limite de vagas (BE-016), pauta alfabética (BE-017) e status/auditoria (BE-019)."""
    coord_user, coord_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="enr_crd",
        full_name="Secretaria Acadêmica SENAI",
        registration_number="SENAI-SEC-001",
    )
    teacher_user, teacher_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.TEACHER,
        suffix="enr_tch",
        full_name="Prof. Metrologia",
        registration_number="SENAI-DOC-020",
    )
    student_z, _ = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="enr_stuz",
        full_name="Carlos Eduardo Rocha",
        registration_number="SENAI-ALU-2026-002",
    )
    student_a, _ = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="enr_stua",
        full_name="Álvaro Mendes Costa",
        registration_number="SENAI-ALU-2026-001",
    )
    student_b, _ = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.STUDENT,
        suffix="enr_stub",
        full_name="Beatriz Helena Silva",
        registration_number="SENAI-ALU-2026-003",
    )

    course_id = (
        await async_client.post(
            "/api/v1/courses",
            json={"code": "TEC-AUT-01", "name": "Técnico em Automação", "total_hours": 1200},
            headers=coord_headers,
        )
    ).json()["id"]
    class_id = (
        await async_client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "code": "AUT-2026-1",
                "period": "2026.1",
                "shift": "NIGHT",
                "max_students": 2,
                "status": "ACTIVE",
                "start_date": "2026-02-09",
                "end_date": "2026-07-10",
            },
            headers=coord_headers,
        )
    ).json()["id"]
    subject_id = (
        await async_client.post(
            "/api/v1/subjects",
            json={
                "course_id": course_id,
                "code": "UC-CLP-01",
                "name": "Controladores Lógicos Programáveis",
                "workload_hours": 80,
            },
            headers=coord_headers,
        )
    ).json()["id"]
    assert (
        await async_client.post(
            "/api/v1/teacher-assignments",
            json={"teacher_id": str(teacher_user.id), "class_id": class_id, "subject_id": subject_id},
            headers=coord_headers,
        )
    ).status_code == status.HTTP_201_CREATED

    # Matricula 2 alunos (inseridos fora de ordem alfabética: Carlos depois Álvaro)
    res_enr_z = await async_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_z.id), "class_id": class_id},
        headers=coord_headers,
    )
    res_enr_a = await async_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_a.id), "class_id": class_id},
        headers=coord_headers,
    )
    assert res_enr_z.status_code == status.HTTP_201_CREATED
    assert res_enr_a.status_code == status.HTTP_201_CREATED
    enr_z_id = res_enr_z.json()["id"]

    # Duplicidade -> HTTP 409; 3º estudante com turma lotada (max_students=2) -> HTTP 422
    res_dup = await async_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_a.id), "class_id": class_id},
        headers=coord_headers,
    )
    assert res_dup.status_code == status.HTTP_409_CONFLICT
    assert res_dup.json()["message"] == ENROLLMENT_ALREADY_EXISTS_MESSAGE

    res_full = await async_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_b.id), "class_id": class_id},
        headers=coord_headers,
    )
    assert res_full.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_full.json()["message"] == ENROLLMENT_CLASS_FULL_MESSAGE

    # Pauta da turma via professor alocado: ordem alfabética e 0 vagas disponíveis
    res_roster = await async_client.get(
        f"/api/v1/classes/{class_id}/students",
        headers=teacher_headers,
    )
    assert res_roster.status_code == status.HTTP_200_OK
    roster_body = res_roster.json()
    assert roster_body["total"] == 2
    assert roster_body["academic_class"]["enrolled_students_count"] == 2
    assert roster_body["academic_class"]["available_slots"] == 0
    assert [s["full_name"] for s in roster_body["data"]] == [
        "Álvaro Mendes Costa",
        "Carlos Eduardo Rocha",
    ]

    # Trancamento (DROPPED) gera audit_logs e libera 1 vaga para Beatriz
    res_drop = await async_client.patch(
        f"/api/v1/enrollments/{enr_z_id}/status",
        json={"status": "DROPPED", "justification": "Transferência de turno solicitada."},
        headers=coord_headers,
    )
    assert res_drop.status_code == status.HTTP_200_OK
    assert res_drop.json()["status"] == "DROPPED"

    audit_record = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity == "enrollments",
            AuditLog.entity_id == enr_z_id,
        )
    )
    assert audit_record is not None
    assert audit_record.user_id == coord_user.id
    assert audit_record.old_values is not None and audit_record.old_values["status"] == "ACTIVE"
    assert audit_record.new_values is not None
    assert audit_record.new_values["status"] == "DROPPED"
    assert audit_record.new_values["justification"] == "Transferência de turno solicitada."

    # Aluno DROPPED não impacta chamada / cálculo de faltas futuras
    eligible = EnrollmentRepository(session=db_session).list_eligible_for_attendance(UUID(class_id))
    assert [item.student_id for item in eligible] == [student_a.id]

    res_enr_b = await async_client.post(
        "/api/v1/enrollments",
        json={"student_id": str(student_b.id), "class_id": class_id},
        headers=coord_headers,
    )
    assert res_enr_b.status_code == status.HTTP_201_CREATED


async def test_academic_domain_constraints_deactivation_guards_and_lifecycle(
    async_client: AsyncClient,
    db_session: Session,
    fast_hasher: PasswordHasher,
) -> None:
    """Valida proteção contra desativação de curso com turma ativa e ciclo de vida completo."""
    _, coord_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.COORDINATOR,
        suffix="grd_crd",
        full_name="Coordenador Governança",
        registration_number="SENAI-CRD-999",
    )
    _, admin_headers = _create_user_with_token(
        db_session,
        fast_hasher,
        role=UserRole.ADMIN,
        suffix="grd_adm",
        full_name="Administrador Governança",
        registration_number="SENAI-ADM-999",
    )

    course_id = (
        await async_client.post(
            "/api/v1/courses",
            json={"code": "TEC-LOG-01", "name": "Técnico em Logística", "total_hours": 800},
            headers=coord_headers,
        )
    ).json()["id"]
    class_id = (
        await async_client.post(
            "/api/v1/classes",
            json={
                "course_id": course_id,
                "code": "LOG-2026-1",
                "period": "2026.1",
                "shift": "MORNING",
                "status": "ACTIVE",
                "start_date": "2026-02-09",
                "end_date": "2026-07-10",
            },
            headers=coord_headers,
        )
    ).json()["id"]

    # Curso com turma ACTIVE não pode ser desativado (HTTP 409)
    res_block_del = await async_client.delete(
        f"/api/v1/courses/{course_id}",
        headers=coord_headers,
    )
    assert res_block_del.status_code == status.HTTP_409_CONFLICT
    assert res_block_del.json()["message"] == COURSE_DEACTIVATION_ACTIVE_CLASSES_MESSAGE

    # Conclui turma -> apenas ADMIN pode reabrir; após concluída, soft delete do curso é liberado
    res_complete = await async_client.patch(
        f"/api/v1/classes/{class_id}/status",
        json={"status": "COMPLETED"},
        headers=coord_headers,
    )
    assert res_complete.status_code == status.HTTP_200_OK

    res_reopen_denied = await async_client.patch(
        f"/api/v1/classes/{class_id}/status",
        json={"status": "ACTIVE"},
        headers=coord_headers,
    )
    assert res_reopen_denied.status_code == status.HTTP_403_FORBIDDEN

    res_reopen_admin = await async_client.patch(
        f"/api/v1/classes/{class_id}/status",
        json={"status": "ACTIVE"},
        headers=admin_headers,
    )
    assert res_reopen_admin.status_code == status.HTTP_200_OK

    assert (
        await async_client.patch(
            f"/api/v1/classes/{class_id}/status",
            json={"status": "ARCHIVED"},
            headers=coord_headers,
        )
    ).status_code == status.HTTP_200_OK

    res_del_ok = await async_client.delete(
        f"/api/v1/courses/{course_id}",
        headers=coord_headers,
    )
    assert res_del_ok.status_code == status.HTTP_200_OK
    assert res_del_ok.json()["is_active"] is False


async def test_nested_transaction_rollback_isolation_leaves_clean_database(
    db_session: Session,
) -> None:
    """Critério de Aceitação: Garante que o rollback da transação aninhada limpa 100% os dados após cada teste."""
    for model in (
        Course,
        AcademicClass,
        Subject,
        LearningModule,
        Competency,
        Enrollment,
        TeacherAssignment,
        AuditLog,
        User,
    ):
        row_count = int(db_session.scalar(select(func.count()).select_from(model)) or 0)
        assert row_count == 0, f"Tabela {model.__tablename__} manteve registros residuais entre testes!"
