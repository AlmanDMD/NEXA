"""Camada de schemas (contratos Pydantic de entrada e saída)."""

from app.schemas.error import ErrorDetail, ErrorResponse
from app.schemas.health import HealthResponse

__all__ = ["ErrorDetail", "ErrorResponse", "HealthResponse"]
