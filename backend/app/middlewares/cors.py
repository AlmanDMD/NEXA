from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings


def setup_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """Configura o middleware de CORS com parâmetros vindos do pydantic-settings."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

