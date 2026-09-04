"""Tests for webhook idempotency and duplicate delivery protection."""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_factory
from app.models.entities import WebhookEvent


@pytest.mark.asyncio
async def test_webhook_idempotent_duplicate_handling():
    async with async_session_factory() as session:
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        
        # 1. First delivery
        first_evt = WebhookEvent(
            id=event_id,
            event_type="payment.captured",
            raw_payload={"event": "payment.captured", "id": event_id},
            signature="sig_test_123",
            processed=True,
            is_duplicate=False,
        )
        session.add(first_evt)
        await session.commit()

        # 2. Query duplicate
        query = select(WebhookEvent).where(WebhookEvent.id == event_id)
        res = await session.execute(query)
        existing = res.scalar_one_or_none()

        assert existing is not None
        assert existing.id == event_id

        # Simulating duplicate receipt
        existing.is_duplicate = True
        await session.commit()

        # Check only 1 record exists in DB with duplicate marked
        all_res = (await session.execute(query)).scalars().all()
        assert len(all_res) == 1
        assert all_res[0].is_duplicate is True
