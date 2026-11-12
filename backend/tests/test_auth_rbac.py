"""Testes unitários e de integração para Dependência de Controle de Acesso por Papel (RBAC - BE-009)."""

from collections.abc import AsyncIterator, Generator
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import (
    PasswordHasher,
    create_access_token,
    get_db,
    get_password_hasher,
    require_role,
)
from app.main import create_app
from app.models import Base, User
from app.repositories.auth_repository import AuthRepository
from app.schemas.enums import UserRole
from app.schemas.user import UserProfileCreateSchema


@pytest.fixture
def db_session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Cria um banco SQLite em memória isolado com todas as tabelas ORM para cada teste."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    try:
        yield testing_session_factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def fast_hasher() -> PasswordHasher:
    """Instância rápida do PasswordHasher (rounds=4) para agilizar os testes de integração."""
    return PasswordHasher(rounds=4)


@pytest.fixture
def rbac_app(
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> FastAPI:
    """Instância FastAPI com rotas protegidas por diferentes regras de RBAC."""
    application = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_password_hasher] = lambda: fast_hasher

    rbac_router = APIRouter(prefix="/api/v1/test-rbac", tags=["Test RBAC"])

    # Rota exclusiva para professores (lançamento de notas / planos de aula)
    @rbac_router.post(
        "/grades",
        dependencies=[Depends(require_role(UserRole.TEACHER))],
    )
    async def post_grades() -> dict[str, str]:
        return {"status": "success", "message": "Notas registradas com sucesso."}

    # Rota exclusiva para coordenadores e administradores (criação de turmas / gestão)
    @rbac_router.post(
        "/classes",
        dependencies=[Depends(require_role("ADMIN", "COORDINATOR"))],
    )
    async def create_class() -> dict[str, str]:
        return {"status": "success", "message": "Turma criada com sucesso."}

    # Rota que injeta o usuário autenticado já validado pelo require_role
    @rbac_router.get(
        "/teacher-profile",
    )
    async def get_teacher_profile(
        current_user: User = Depends(require_role("TEACHER")),
    ) -> dict[str, Any]:
        return {
            "email": current_user.email,
            "role": current_user.role.value,
        }

    # Rota com múltiplos papéis misturando enum e strings em caixas variadas
    @rbac_router.get(
        "/pedagogical-council",
        dependencies=[Depends(require_role(UserRole.COORDINATOR, "teacher", "admin"))],
    )
    async def get_council_agenda() -> dict[str, str]:
        return {"status": "success", "message": "Pauta do conselho liberada."}

    application.include_router(rbac_router)
    return application


@pytest.fixture
async def rbac_client(rbac_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP assíncrono para testar as rotas protegidas com RBAC."""
    transport = ASGITransport(app=rbac_app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as client:
        yield client


def _create_user(
    session: Session,
    hasher: PasswordHasher,
    *,
    email: str,
    role: UserRole,
    reg_suffix: str,
) -> User:
    """Helper para persistir usuário de teste."""
    repo = AuthRepository(session=session)
    profile_data = UserProfileCreateSchema(
        full_name=f"Usuário {role.value}",
        registration_number=f"SENAI-{role.value[:3]}-{reg_suffix}",
        phone="(11) 98888-7777",
    )
    return repo.create_user(
        email=email,
        password_hash=hasher.hash_password("Senai@2026!Secret"),
        role=role,
        is_active=True,
        profile_data=profile_data,
    )


def test_require_role_factory_rejects_empty_roles() -> None:
    """Valida se a factory require_role rejeita chamada sem papéis com ValueError."""
    with pytest.raises(ValueError, match="Pelo menos um papel deve ser informado"):
        require_role()


def test_require_role_unit_direct_invocation() -> None:
    """Valida comportamento unitário puro da dependência require_role."""
    checker = require_role("TEACHER", UserRole.COORDINATOR)

    # Mock simples de usuário
    class FakeUser:
        def __init__(self, role: Any) -> None:
            self.role = role

    teacher = FakeUser(UserRole.TEACHER)
    coord = FakeUser("COORDINATOR")
    student = FakeUser(UserRole.STUDENT)
    admin = FakeUser("ADMIN")

    # Papéis autorizados retornam o usuário
    assert checker(current_user=teacher) is teacher
    assert checker(current_user=coord) is coord

    # Papéis não autorizados lançam HTTPException com status 403
    with pytest.raises(HTTPException) as exc_info_student:
        checker(current_user=student)
    assert exc_info_student.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info_student.value.detail == "Acesso não autorizado para seu perfil"

    with pytest.raises(HTTPException) as exc_info_admin:
        checker(current_user=admin)
    assert exc_info_admin.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info_admin.value.detail == "Acesso não autorizado para seu perfil"


async def test_student_blocked_from_teacher_exclusive_route(
    rbac_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Aluno tentando acessar rota exclusiva de Professor recebe 403 Forbidden."""
    with db_session_factory() as session:
        student = _create_user(
            session,
            fast_hasher,
            email="aluno.teste@senai.br",
            role=UserRole.STUDENT,
            reg_suffix="001",
        )
        student_id = student.id

    token = create_access_token(
        subject=student_id,
        email="aluno.teste@senai.br",
        role=UserRole.STUDENT,
    )

    response = await rbac_client.post(
        "/api/v1/test-rbac/grades",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == status.HTTP_403_FORBIDDEN
    assert body["error"] == "FORBIDDEN"
    assert body["message"] == "Acesso não autorizado para seu perfil"


async def test_teacher_allowed_in_teacher_exclusive_route(
    rbac_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que Professor acessa rota exclusiva com HTTP 200 OK."""
    with db_session_factory() as session:
        teacher = _create_user(
            session,
            fast_hasher,
            email="professor.teste@senai.br",
            role=UserRole.TEACHER,
            reg_suffix="002",
        )
        teacher_id = teacher.id

    token = create_access_token(
        subject=teacher_id,
        email="professor.teste@senai.br",
        role=UserRole.TEACHER,
    )

    response = await rbac_client.post(
        "/api/v1/test-rbac/grades",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "success"
    assert body["message"] == "Notas registradas com sucesso."


async def test_multiple_roles_admin_and_coordinator_access(
    rbac_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Critério de Aceitação: Suporte a múltiplos papéis (ex: ADMIN e COORDINATOR)."""
    with db_session_factory() as session:
        admin = _create_user(
            session,
            fast_hasher,
            email="admin.teste@senai.br",
            role=UserRole.ADMIN,
            reg_suffix="003",
        )
        coord = _create_user(
            session,
            fast_hasher,
            email="coord.teste@senai.br",
            role=UserRole.COORDINATOR,
            reg_suffix="004",
        )
        teacher = _create_user(
            session,
            fast_hasher,
            email="prof.bloqueado@senai.br",
            role=UserRole.TEACHER,
            reg_suffix="005",
        )
        student = _create_user(
            session,
            fast_hasher,
            email="aluno.bloqueado@senai.br",
            role=UserRole.STUDENT,
            reg_suffix="006",
        )
        admin_id = admin.id
        coord_id = coord.id
        teacher_id = teacher.id
        student_id = student.id

    # 1. Admin acessa criação de turmas -> OK
    admin_token = create_access_token(subject=admin_id, role=UserRole.ADMIN)
    res_admin = await rbac_client.post(
        "/api/v1/test-rbac/classes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == status.HTTP_200_OK

    # 2. Coordenador acessa criação de turmas -> OK
    coord_token = create_access_token(subject=coord_id, role=UserRole.COORDINATOR)
    res_coord = await rbac_client.post(
        "/api/v1/test-rbac/classes",
        headers={"Authorization": f"Bearer {coord_token}"},
    )
    assert res_coord.status_code == status.HTTP_200_OK

    # 3. Professor é bloqueado na criação de turmas -> 403
    teacher_token = create_access_token(subject=teacher_id, role=UserRole.TEACHER)
    res_teacher = await rbac_client.post(
        "/api/v1/test-rbac/classes",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_teacher.status_code == status.HTTP_403_FORBIDDEN
    assert res_teacher.json()["message"] == "Acesso não autorizado para seu perfil"

    # 4. Aluno é bloqueado na criação de turmas -> 403
    student_token = create_access_token(subject=student_id, role=UserRole.STUDENT)
    res_student = await rbac_client.post(
        "/api/v1/test-rbac/classes",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == status.HTTP_403_FORBIDDEN
    assert res_student.json()["message"] == "Acesso não autorizado para seu perfil"


async def test_require_role_injects_user_as_parameter_dependency(
    rbac_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Valida injeção de dependência direta no parâmetro da função da rota (current_user: User = Depends(require_role(...)))."""
    with db_session_factory() as session:
        teacher = _create_user(
            session,
            fast_hasher,
            email="docente.mecanica@senai.br",
            role=UserRole.TEACHER,
            reg_suffix="007",
        )
        teacher_id = teacher.id

    token = create_access_token(subject=teacher_id, role=UserRole.TEACHER)
    response = await rbac_client.get(
        "/api/v1/test-rbac/teacher-profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["email"] == "docente.mecanica@senai.br"
    assert body["role"] == "TEACHER"


async def test_require_role_normalizes_case_and_mixed_types(
    rbac_client: AsyncClient,
    db_session_factory: sessionmaker[Session],
    fast_hasher: PasswordHasher,
) -> None:
    """Garante que require_role normaliza case ('teacher', 'admin') e aceita enums misturados."""
    with db_session_factory() as session:
        teacher = _create_user(
            session,
            fast_hasher,
            email="prof.conselho@senai.br",
            role=UserRole.TEACHER,
            reg_suffix="008",
        )
        student = _create_user(
            session,
            fast_hasher,
            email="aluno.conselho@senai.br",
            role=UserRole.STUDENT,
            reg_suffix="009",
        )
        teacher_id = teacher.id
        student_id = student.id

    teacher_token = create_access_token(subject=teacher_id, role=UserRole.TEACHER)
    student_token = create_access_token(subject=student_id, role=UserRole.STUDENT)

    # Professor autorizado (definido como string minúscula 'teacher')
    res_teacher = await rbac_client.get(
        "/api/v1/test-rbac/pedagogical-council",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_teacher.status_code == status.HTTP_200_OK

    # Aluno bloqueado
    res_student = await rbac_client.get(
        "/api/v1/test-rbac/pedagogical-council",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == status.HTTP_403_FORBIDDEN


async def test_require_role_blocks_unauthenticated_requests_with_401(
    rbac_client: AsyncClient,
) -> None:
    """Garante que requisição sem autenticação falha em get_current_user com 401 antes da checagem de papel."""
    response = await rbac_client.post("/api/v1/test-rbac/grades")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
