from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn

from app.core.config import get_settings
from app.middlewares.cors import setup_cors_middleware
from app.routers.health import router as health_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gerencia o ciclo de vida (startup e shutdown) da aplicação."""
    settings = get_settings()
    logger.info(
        "Iniciando %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    app.state.settings = settings
    yield
    logger.info("Encerrando %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Factory de criação e configuração da instância FastAPI."""
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

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

