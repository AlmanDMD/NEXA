from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema de resposta do endpoint de verificação de saúde."""

    status: str = Field(default="ok", examples=["ok"])
    timestamp: datetime = Field(description="Timestamp atual em UTC (ISO 8601)")

