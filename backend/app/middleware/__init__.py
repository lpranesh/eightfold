"""Error handling middleware — translates exceptions to HTTP responses."""

import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import BaseApplicationException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(BaseApplicationException)
    async def handle_application_exception(
        request: Request, exc: BaseApplicationException,
    ) -> JSONResponse:
        logger.warning(
            "Application error: %s",
            exc.message,
            extra={"status_code": exc.status_code, "details": exc.details},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "detail": exc.details if exc.details else None,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(
        request: Request, exc: Exception,
    ) -> JSONResponse:
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": None,
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
