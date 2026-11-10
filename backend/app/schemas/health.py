from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseResponseSchema


class HealthResponse(BaseResponseSchema):
    """Schema de resposta do endpoint de verificação de saúde."""

    status: str = Field(default="ok", examples=["ok"])
    timestamp: datetime = Field(description="Timestamp atual em UTC (ISO 8601)")


