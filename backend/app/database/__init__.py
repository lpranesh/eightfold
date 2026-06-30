"""Database session management and engine configuration."""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import Settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages async SQLAlchemy engine and session factory.

    Uses dependency injection — the Settings object is passed in,
    not imported globally.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.database_echo,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a database session, ensuring cleanup on exit.

        Yields:
            An async database session.
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def check_health(self) -> bool:
        """Check database connectivity.

        Returns:
            True if the database is reachable.
        """
        try:
            async with self._session_factory() as session:
                await session.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            return True
        except Exception as exc:
            logger.error("Database health check failed", exc_info=exc)
            return False

    async def init_db(self) -> None:
        """Create database tables."""
        from app.models.database import Base
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Dispose of the engine connection pool."""
        await self._engine.dispose()
