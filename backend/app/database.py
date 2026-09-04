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
            tables = inspector.get_table_names()

            if "recovery_predictions" in tables:
                cols = [c["name"] for c in inspector.get_columns("recovery_predictions")]
                if "feature_schema_version" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_predictions ADD COLUMN feature_schema_version VARCHAR(32) DEFAULT 'v1.0'"))
                if "correlation_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_predictions ADD COLUMN correlation_id VARCHAR(128)"))

            if "recovery_decisions" in tables:
                cols = [c["name"] for c in inspector.get_columns("recovery_decisions")]
                if "agent_run_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_decisions ADD COLUMN agent_run_id VARCHAR(64)"))
                if "strategy" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_decisions ADD COLUMN strategy VARCHAR(64)"))
                if "reason" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_decisions ADD COLUMN reason TEXT"))
                if "policy_status" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_decisions ADD COLUMN policy_status VARCHAR(32)"))
                if "policy_reason" not in cols:
                    sync_conn.execute(text("ALTER TABLE recovery_decisions ADD COLUMN policy_reason TEXT"))

            if "execution_records" in tables:
                cols = [c["name"] for c in inspector.get_columns("execution_records")]
                if "strategy" not in cols:
                    sync_conn.execute(text("ALTER TABLE execution_records ADD COLUMN strategy VARCHAR(64)"))
                if "authorization_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE execution_records ADD COLUMN authorization_id VARCHAR(64)"))

            if "verification_records" in tables:
                cols = [c["name"] for c in inspector.get_columns("verification_records")]
                if "api_verified" not in cols:
                    sync_conn.execute(text("ALTER TABLE verification_records ADD COLUMN api_verified BOOLEAN DEFAULT 0"))
                if "webhook_verified" not in cols:
                    sync_conn.execute(text("ALTER TABLE verification_records ADD COLUMN webhook_verified BOOLEAN DEFAULT 0"))
                if "signals_agree" not in cols:
                    sync_conn.execute(text("ALTER TABLE verification_records ADD COLUMN signals_agree BOOLEAN DEFAULT 0"))
                if "api_evidence_hash" not in cols:
                    sync_conn.execute(text("ALTER TABLE verification_records ADD COLUMN api_evidence_hash VARCHAR(64)"))
                if "webhook_evidence_hash" not in cols:
                    sync_conn.execute(text("ALTER TABLE verification_records ADD COLUMN webhook_evidence_hash VARCHAR(64)"))

            if "audit_logs" in tables:
                cols = [c["name"] for c in inspector.get_columns("audit_logs")]
                if "correlation_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN correlation_id VARCHAR(64)"))
                if "agent_id" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN agent_id VARCHAR(64)"))
                if "event_type" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN event_type VARCHAR(64)"))
                if "input_hash" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN input_hash VARCHAR(64)"))
                if "output_hash" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN output_hash VARCHAR(64)"))
                if "policy_version" not in cols:
                    sync_conn.execute(text("ALTER TABLE audit_logs ADD COLUMN policy_version VARCHAR(32)"))

        await conn.run_sync(migrate_sqlite_columns)


async def close_db() -> None:
    """Dispose engine connections on shutdown."""
    await engine.dispose()
