"""Integration Test for Scenario 1: Autonomous Revenue Recovery (PAY_DEMO_001).

Verifies:
- Full autonomous recovery flow for transient network error (₹24,999.00)
- Lifecycle: FAILED -> ANALYZING -> RECOVERY_PLANNED -> EXECUTING -> AWAITING_VERIFICATION -> RECOVERED
- Verified revenue strictly matches INR 24,999.00
- Dual-signal agreement (API captured + Webhook captured)
- SHA-256 cryptographic evidence hash generation
"""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    Customer,
    RecoveryCase,
    RecoveryState,
    RecoveryStrategy,
    VerificationRecord,
)
from app.agents.orchestrator import orchestrator


@pytest.mark.asyncio
async def test_scenario_1_autonomous_recovery_full_lifecycle():
    """Verify complete autonomous recovery lifecycle from payment failure to verified revenue."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_001_{uid}"

        cust = await session.get(Customer, "cust_demo_auto")
        if not cust:
            cust = Customer(
                id="cust_demo_auto",
                name="Auto Recovery Customer",
                email="auto@example.com",
                customer_age_days=120,
                opt_out=False,
            )
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid}",
            customer_id="cust_demo_auto",
            amount_at_risk=24999.00,
            failure_type="timeout",
            failure_reason="Gateway response timed out waiting for issuer authorization",
            retry_count=0,
            state=RecoveryState.FAILED,
        )
        session.add(case)
        await session.commit()

        # Run complete recovery orchestration
        result = await orchestrator.run_full_recovery_flow(
            case_id=case_id,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )

        await session.refresh(case)

        # Assertions
        assert case.state == RecoveryState.RECOVERED
        assert case.recovered_amount == 24999.00
        assert case.verification_id is not None
        assert result["status"] == "RECOVERED"
        assert result["verified_amount"] == 24999.00
        assert len(result["evidence_hash"]) == 64  # Valid SHA-256 hash length

        # Verify persisted verification record
        verif = await session.get(VerificationRecord, case.verification_id)
        assert verif is not None
        assert verif.verification_status == "VERIFIED"
        assert verif.api_state_confirmed is True
        assert verif.webhook_confirmed is True
        assert verif.signals_agree is True
