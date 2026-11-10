from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import logger, setup_logging
from app.middlewares.cors import setup_cors_middleware
from app.routers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gerencia o ciclo de vida (startup e shutdown) da aplicação."""
    settings = get_settings()
    logger.bind(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    ).info(
        f"Iniciando {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]"
    )
    app.state.settings = settings
    yield
    logger.bind(app_name=settings.APP_NAME).info(f"Encerrando {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Factory de criação e configuração da instância FastAPI."""
    settings = get_settings()
    setup_logging(settings)

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    register_exception_handlers(application)
    setup_cors_middleware(application, settings)
    application.include_router(health_router)

    return application


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
