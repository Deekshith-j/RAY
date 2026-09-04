from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


# Configure engine options based on dialect
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    future=True,
    connect_args=connect_args,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize all tables in the database and handle schema updates."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        def migrate_sqlite_columns(sync_conn):
            from sqlalchemy import inspect, text
            inspector = inspect(sync_conn)
            if "recovery_predictions" in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns("recovery_predictions")]
                if "feature_schema_version" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_predictions ADD COLUMN feature_schema_version VARCHAR(32) DEFAULT 'v1.0'"))
                if "correlation_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_predictions ADD COLUMN correlation_id VARCHAR(128)"))

        await conn.run_sync(migrate_sqlite_columns)


async def close_db() -> None:
    """Dispose engine connections on shutdown."""
    await engine.dispose()
