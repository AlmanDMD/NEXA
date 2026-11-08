"""Schemas Pydantic para respostas padronizadas de erro da API."""

from typing import Any

from pydantic import Field

from app.schemas.base import BaseResponseSchema


class ErrorDetail(BaseResponseSchema):
    """Detalhe individual de erro (ex: campo inválido na validação)."""

    field: str = Field(description="Nome ou caminho do campo com erro", examples=["email"])
    message: str = Field(
        description="Mensagem amigável descrevendo o problema no campo",
        examples=["Campo obrigatório."],
    )
    type: str | None = Field(
        default=None,
        description="Código identificador do tipo de erro de validação",
        examples=["missing"],
    )


class ErrorResponse(BaseResponseSchema):
    """Contrato padronizado de resposta de erro da API NEXA."""

    success: bool = Field(default=False, description="Indica falha na requisição", examples=[False])
    status_code: int = Field(description="Código de status HTTP", examples=[400])
    error: str = Field(description="Código identificador do erro", examples=["VALIDATION_ERROR"])
    message: str = Field(
        description="Mensagem principal legível para o cliente",
        examples=["Erro de validação nos dados enviados. Verifique os campos informados."],
    )
    details: list[ErrorDetail | dict[str, Any]] | None = Field(
        default=None,
        description="Lista opcional de detalhes ou campos inválidos",
    )

