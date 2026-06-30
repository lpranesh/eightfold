"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.controllers import router, set_dependencies
from app.config.settings import Settings
from app.database import DatabaseManager
from app.middleware import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    # Startup
    settings = Settings()
    db_manager = DatabaseManager(settings)
    set_dependencies(db_manager, settings)
    logger.info(
        "Application started: %s v%s (%s)",
        settings.app_name, settings.app_version, settings.environment.value,
    )
    yield
    # Shutdown
    await db_manager.close()
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Candidate Data Transformer",
        description="Multi-source candidate data transformation with provenance tracking",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(router, prefix="/api")

    return app


app = create_app()
