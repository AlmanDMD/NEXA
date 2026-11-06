"""Testes unitários e de integração para Exception Handlers Globais e Logs Estruturados (BE-002)."""

import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict, Field, field_validator
import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.core.config import Settings
from app.core.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    UnauthorizedException,
    UnprocessableEntityException,
)
from app.core.logging import logger, setup_logging
from app.main import create_app


class SamplePayload(BaseModel):
    """Schema de exemplo para testar validação Pydantic v2."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=100)
    age: int = Field(ge=14, le=120)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("O endereço de e-mail deve conter '@'.")
        return value


@pytest.fixture
def test_app() -> FastAPI:
    """Cria uma instância FastAPI isolada com rotas de teste para cada cenário de exceção."""
    app = create_app()

    @app.post("/test/validation")
    async def route_validation(
        payload: SamplePayload,
        page: int = Query(default=1, ge=1),
    ) -> dict[str, Any]:
        return {"email": payload.email, "age": payload.age, "page": page}

    @app.get("/test/bad-request")
    async def route_bad_request() -> None:
        raise BadRequestException(
            message="Parâmetros de filtro inválidos.",
            details=[{"field": "start_date", "message": "Data inicial maior que a final."}],
        )

    @app.get("/test/unauthorized")
    async def route_unauthorized() -> None:
        raise UnauthorizedException(message="Token de autenticação expirado ou inválido.")

    @app.get("/test/forbidden")
    async def route_forbidden() -> None:
        raise ForbiddenException(message="Acesso não autorizado para seu perfil.")

    @app.get("/test/not-found")
    async def route_not_found() -> None:
        raise NotFoundException(message="Aluno não encontrado na turma informada.")

    @app.get("/test/conflict")
    async def route_conflict() -> None:
        raise ConflictException(message="Matrícula já existente para este estudante.")

    @app.get("/test/unprocessable")
    async def route_unprocessable() -> None:
        raise UnprocessableEntityException(message="Período letivo encerrado para esta turma.")

    @app.get("/test/internal-app-error")
    async def route_internal_app_error() -> None:
        raise InternalServerException()

    @app.get("/test/http-exception-403")
    async def route_http_exception_403() -> None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado para seu perfil",
        )

    @app.get("/test/sqlalchemy-unique")
    async def route_sqlalchemy_unique() -> None:
        class FakeOrigError(Exception):
            pgcode = "23505"

        raise IntegrityError(
            statement="INSERT INTO users (email, password_hash) VALUES ('a@b.com', 'secret')",
            params={"email": "a@b.com"},
            orig=FakeOrigError("duplicate key value violates unique constraint 'uq_users_email'"),
        )

    @app.get("/test/sqlalchemy-fk")
    async def route_sqlalchemy_fk() -> None:
        class FakeOrigError(Exception):
            pgcode = "23503"

        raise IntegrityError(
            statement="DELETE FROM courses WHERE id = 1",
            params={"id": 1},
            orig=FakeOrigError("update or delete on table violates foreign key constraint"),
        )

    @app.get("/test/sqlalchemy-generic")
    async def route_sqlalchemy_generic() -> None:
        raise OperationalError(
            statement="SELECT * FROM secret_internal_table WHERE token = 'super-secret'",
            params={},
            orig=Exception("connection to server at '10.0.0.55' port 5432 failed"),
        )

    @app.get("/test/unhandled-500")
    async def route_unhandled_500() -> None:
        raise RuntimeError("Falha crítica interna em /var/lib/postgresql/data: senha_banco=123456")

    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncClient:
    """Cliente HTTP assíncrono acoplado à aplicação FastAPI de teste."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def test_validation_error_returns_400_with_friendly_field_list(client: AsyncClient) -> None:
    """Erros de validação Pydantic devem retornar HTTP 400 e lista amigável de campos inválidos."""
    response = await client.post(
        "/test/validation?page=0",
        json={"email": "ab", "age": "nao-inteiro", "campo_extra": "invalido"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()

    assert body["success"] is False
    assert body["status_code"] == 400
    assert body["error"] == "VALIDATION_ERROR"
    assert isinstance(body["message"], str) and len(body["message"]) > 0
    assert isinstance(body["details"], list)

    fields_with_error = {item["field"]: item["message"] for item in body["details"]}
    assert "page" in fields_with_error
    assert "email" in fields_with_error
    assert "age" in fields_with_error
    assert "campo_extra" in fields_with_error
    assert "pelo menos 5 caracteres" in fields_with_error["email"]
    assert "número inteiro válido" in fields_with_error["age"]
    assert "Campo adicional não permitido" in fields_with_error["campo_extra"]


async def test_custom_field_validator_error_returns_400_in_portuguese(client: AsyncClient) -> None:
    """Validadores customizados (@field_validator) devem retornar HTTP 400 sem prefixo 'Value error,'."""
    response = await client.post(
        "/test/validation",
        json={"email": "email_sem_arroba", "age": 20},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["success"] is False
    assert body["status_code"] == 400
    assert body["details"][0]["field"] == "email"
    assert body["details"][0]["message"] == "O endereço de e-mail deve conter '@'."


async def test_bad_request_exception_400(client: AsyncClient) -> None:
    """Testa cenário HTTP 400 via BadRequestException."""
    response = await client.get("/test/bad-request")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body == {
        "success": False,
        "status_code": 400,
        "error": "BAD_REQUEST",
        "message": "Parâmetros de filtro inválidos.",
        "details": [{"field": "start_date", "message": "Data inicial maior que a final."}],
    }


async def test_unauthorized_exception_401(client: AsyncClient) -> None:
    """Testa cenário HTTP 401 via UnauthorizedException."""
    response = await client.get("/test/unauthorized")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body == {
        "success": False,
        "status_code": 401,
        "error": "UNAUTHORIZED",
        "message": "Token de autenticação expirado ou inválido.",
    }


async def test_forbidden_exception_403(client: AsyncClient) -> None:
    """Testa cenário HTTP 403 via ForbiddenException e HTTPException."""
    response_app = await client.get("/test/forbidden")
    assert response_app.status_code == status.HTTP_403_FORBIDDEN
    assert response_app.json() == {
        "success": False,
        "status_code": 403,
        "error": "FORBIDDEN",
        "message": "Acesso não autorizado para seu perfil.",
    }

    response_http = await client.get("/test/http-exception-403")
    assert response_http.status_code == status.HTTP_403_FORBIDDEN
    assert response_http.json() == {
        "success": False,
        "status_code": 403,
        "error": "FORBIDDEN",
        "message": "Acesso não autorizado para seu perfil",
    }


async def test_not_found_exception_404_and_unknown_route(client: AsyncClient) -> None:
    """Testa cenário HTTP 404 via NotFoundException e rota inexistente do FastAPI."""
    response_domain = await client.get("/test/not-found")
    assert response_domain.status_code == status.HTTP_404_NOT_FOUND
    assert response_domain.json() == {
        "success": False,
        "status_code": 404,
        "error": "NOT_FOUND",
        "message": "Aluno não encontrado na turma informada.",
    }

    response_route = await client.get("/rota-que-nao-existe")
    assert response_route.status_code == status.HTTP_404_NOT_FOUND
    assert response_route.json() == {
        "success": False,
        "status_code": 404,
        "error": "NOT_FOUND",
        "message": "Recurso não encontrado.",
    }


async def test_conflict_and_unprocessable_exceptions(client: AsyncClient) -> None:
    """Testa cenários HTTP 409 e HTTP 422 via subclasses de AppException."""
    res_409 = await client.get("/test/conflict")
    assert res_409.status_code == status.HTTP_409_CONFLICT
    assert res_409.json()["error"] == "CONFLICT"

    res_422 = await client.get("/test/unprocessable")
    assert res_422.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert res_422.json()["error"] == "UNPROCESSABLE_ENTITY"


async def test_sqlalchemy_errors_do_not_leak_sql_or_infra_details(client: AsyncClient) -> None:
    """Garante que erros do SQLAlchemy (IntegrityError e OperationalError) nunca vazem SQL cru."""
    res_unique = await client.get("/test/sqlalchemy-unique")
    assert res_unique.status_code == status.HTTP_409_CONFLICT
    body_unique = res_unique.json()
    assert body_unique["success"] is False
    assert body_unique["status_code"] == 409
    assert body_unique["error"] == "CONFLICT"
    assert "INSERT INTO" not in json.dumps(body_unique)
    assert "uq_users_email" not in json.dumps(body_unique)

    res_fk = await client.get("/test/sqlalchemy-fk")
    assert res_fk.status_code == status.HTTP_409_CONFLICT
    body_fk = res_fk.json()
    assert body_fk["error"] == "FOREIGN_KEY_VIOLATION"
    assert "DELETE FROM" not in json.dumps(body_fk)

    res_generic = await client.get("/test/sqlalchemy-generic")
    assert res_generic.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body_generic = res_generic.json()
    assert body_generic == {
        "success": False,
        "status_code": 500,
        "error": "DATABASE_ERROR",
        "message": "Erro interno ao processar operação no banco de dados.",
    }
    assert "secret_internal_table" not in json.dumps(body_generic)
    assert "10.0.0.55" not in json.dumps(body_generic)


async def test_unhandled_500_logs_structured_json_with_traceback_and_hides_details(
    client: AsyncClient,
) -> None:
    """Exceções 500 inesperadas são logadas em JSON com traceback no servidor e retornam 500 genérico."""
    captured_logs: list[str] = []

    from app.core.logging import format_json_log

    sink_id = logger.add(lambda msg: captured_logs.append(format_json_log(msg.record)), level="ERROR")
    try:
        response = await client.get("/test/unhandled-500")
    finally:
        logger.remove(sink_id)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert body == {
        "success": False,
        "status_code": 500,
        "error": "INTERNAL_SERVER_ERROR",
        "message": "Erro interno inesperado no servidor. Tente novamente mais tarde.",
    }
    assert "senha_banco" not in response.text
    assert "Traceback" not in response.text

    assert len(captured_logs) >= 1
    log_record = json.loads(captured_logs[-1])
    assert log_record["level"] == "ERROR"
    assert log_record["extra"]["status_code"] == 500
    assert log_record["extra"]["error"] == "INTERNAL_SERVER_ERROR"
    assert log_record["extra"]["path"] == "/test/unhandled-500"
    assert log_record["exception"]["type"] == "RuntimeError"
    assert "RuntimeError" in log_record["exception"]["traceback"]


def test_app_exception_inheritance_and_logging_intercept() -> None:
    """Verifica herança de AppException e interceptação de logs padrão pelo Loguru."""
    exc = AppException(message="Erro customizado", status_code=418, error="TEAPOT")
    assert isinstance(exc, Exception)
    assert exc.status_code == 418
    assert exc.error == "TEAPOT"

    settings = Settings(LOG_JSON=True, LOG_LEVEL="INFO")
    setup_logging(settings)

    captured: list[str] = []
    from app.core.logging import format_json_log

    sink_id = logger.add(lambda msg: captured.append(format_json_log(msg.record)), level="INFO")
    try:
        std_logger = logging.getLogger("uvicorn.error")
        std_logger.info("Mensagem interceptada do uvicorn")
    finally:
        logger.remove(sink_id)

    assert len(captured) == 1
    parsed = json.loads(captured[0])
    assert parsed["message"] == "Mensagem interceptada do uvicorn"
    assert parsed["level"] == "INFO"
