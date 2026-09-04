"""Tests for demo reset endpoint behavior."""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_factory
from app.models.entities import RecoveryCase, Customer, RecoveryState
from app.api.v1.recovery import reset_demo_data


@pytest.mark.asyncio
async def test_demo_reset_cleans_only_demo_prefixes():
    async with async_session_factory() as session:
        cid = f"cust_demo_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="reset@test.com", name="Reset Cust", phone="1234567890")
        session.add(cust)

        # 1. Add demo case
        demo_case_id = "PAY_DEMO_TEMP_001"
        case_demo = RecoveryCase(
            id=demo_case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=1000.0,
            failure_type="timeout",
            failure_reason="Demo gateway timeout",
            state=RecoveryState.FAILED,
        )
        session.add(case_demo)

        # 2. Add real / non-demo case
        real_case_id = f"REAL_PROD_CASE_{uuid.uuid4().hex[:8]}"
        case_real = RecoveryCase(
            id=real_case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=5000.0,
            failure_type="timeout",
            failure_reason="Production network issue",
            state=RecoveryState.FAILED,
        )
        session.add(case_real)
        await session.commit()

        # Run demo reset
        res = await reset_demo_data(session)
        assert res["status"] == "success"

        # Verify demo case deleted, real case preserved
        check_demo = await session.get(RecoveryCase, demo_case_id)
        check_real = await session.get(RecoveryCase, real_case_id)

        assert check_demo is None
        assert check_real is not None
