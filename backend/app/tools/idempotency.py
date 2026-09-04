"""Idempotency management for financial recovery operations."""

import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import ExecutionRecord


def generate_idempotency_key(case_id: str, strategy: str, attempt_number: int) -> str:
    """Generate canonical idempotency key: ray:{case_id}:{strategy}:{attempt_number}."""
    sanitized_strategy = strategy.upper().replace(" ", "_")
    return f"ray:{case_id}:{sanitized_strategy}:{attempt_number}"


def validate_idempotency_key_format(key: str) -> bool:
    """Validate that idempotency key adheres to the strict canonical structure."""
    pattern = r"^ray:[a-zA-Z0-9_\-]+:[A-Z_]+:[0-9]+$"
    return bool(re.match(pattern, key))


async def check_idempotency(
    session: AsyncSession,
    idempotency_key: str,
) -> Optional[ExecutionRecord]:
    """
    Check if an operation with this idempotency key has already succeeded or been recorded.
    Returns existing ExecutionRecord if found, preventing duplicate executions.
    """
    stmt = select(ExecutionRecord).where(ExecutionRecord.idempotency_key == idempotency_key)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
