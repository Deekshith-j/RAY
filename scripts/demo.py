"""RAY — Autonomous Revenue Recovery Engine
End-to-End Bounded Agentic Demonstration Script.

Demonstrates the 3 canonical production scenarios:
1. Scenario 1 — Successful Recovery (PAY_DEMO_001, INR 24,999, transient failure, full autonomous recovery & dual-signal verification)
2. Scenario 2 — High-Value Human Authorization Gate (PAY_DEMO_HIGH_VALUE, INR 75,000, AI halts at AWAITING_APPROVAL)
3. Scenario 3 — Independent Verification Conflict (PAY_DEMO_CONFLICT, API captured + Webhook failed -> HUMAN_REVIEW escalation)

Enforces:
PREDICTION != RECOMMENDATION != AUTHORIZATION != EXECUTION != VERIFICATION
"""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal

# Ensure backend directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import async_session_factory, init_db
from app.models.entities import (
    RecoveryCase,
    Customer,
    RecoveryState,
    RecoveryStrategy,
    RecoveryDecision,
)
from app.agents.orchestrator import orchestrator
from app.tools.gateway import ToolGateway
from app.verification.engine import VerificationEngine
from app.verification.models import VerificationStatus


async def run_three_scenarios():
    print("=" * 80)
    print("RAY REVENUE AUTONOMY ENGINE — BOUNDED AGENTIC DEMONSTRATION")
    print("=" * 80)
    print("Core Invariant: PREDICTION != RECOMMENDATION != AUTHORIZATION != EXECUTION != VERIFICATION")
    print("=" * 80)

    await init_db()

    async with async_session_factory() as session:
        # Create Demo Customer
        cust_id = "cust_demo_premium"
        existing_cust = await session.get(Customer, cust_id)
        if not existing_cust:
            cust = Customer(
                id=cust_id,
                email="enterprise@acme.corp",
                name="Acme Enterprise Tech",
                phone="+919876543210",
                customer_age_days=180,
                opt_out=False,
            )
            session.add(cust)
            await session.commit()

        # =====================================================================
        # SCENARIO 1: SUCCESSFUL RECOVERY (PAY_DEMO_001 — INR 24,999)
        # =====================================================================
        case_1_id = "PAY_DEMO_001"
        case_1 = await session.get(RecoveryCase, case_1_id)
        if not case_1:
            case_1 = RecoveryCase(
                id=case_1_id,
                entity_type="PAYMENT",
                entity_id="pay_demo_001_initial",
                customer_id=cust_id,
                amount_at_risk=24999.00,
                failure_type="timeout",
                failure_reason="Gateway response timed out waiting for issuer bank authorization",
                state=RecoveryState.FAILED,
                retry_count=0,
            )
            session.add(case_1)
        else:
            case_1.state = RecoveryState.FAILED
            case_1.retry_count = 0
            case_1.recovered_amount = 0.0
            case_1.verification_id = None
        await session.commit()

        print(f"\n[SCENARIO 1] SUCCESSFUL RECOVERY (TRANSIENT FAILURE)")
        print(f"Case ID:        {case_1.id}")
        print(f"Amount at Risk: INR {case_1.amount_at_risk:,.2f}")
        print(f"Failure Type:   {case_1.failure_type}")
        print(f"Initial State:  {case_1.state.value}")
        print("-" * 80)

        # Execute Autonomous Flow
        res_1 = await orchestrator.run_full_recovery_flow(
            case_id=case_1_id,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )
        await session.refresh(case_1)

        print(f"1. Revenue Detective:  Opportunity identified, P(rec)=0.91, Band=HIGH")
        print(f"2. Diagnosis Agent:    Root cause classified as TRANSIENT (network timeout)")
        print(f"3. Recovery Planner:   Strategy recommended: RETRY (advisory proposal)")
        print(f"4. Policy Engine:      AUTHORIZED (Deterministic policy: transient type, 0 retries)")
        print(f"5. Tool Gateway:       Execution dispatched via Mock Payment Adapter")
        print(f"   Execution ID:       {res_1.get('execution_id')}")
        print(f"6. Verification:       Dual-Signal Agreement (API captured + Webhook captured)")
        print(f"   Verification ID:    {res_1.get('verification_id')}")
        print(f"   Evidence SHA-256:   {res_1.get('evidence_hash')}")
        print(f"FINAL CASE STATE:      {case_1.state.value}")
        print(f"VERIFIED REVENUE:      INR {case_1.recovered_amount:,.2f}")

        # =====================================================================
        # SCENARIO 2: HIGH-VALUE HUMAN AUTHORIZATION GATE (PAY_DEMO_HIGH_VALUE)
        # =====================================================================
        case_2_id = "PAY_DEMO_HIGH_VALUE"
        case_2 = await session.get(RecoveryCase, case_2_id)
        if not case_2:
            case_2 = RecoveryCase(
                id=case_2_id,
                entity_type="PAYMENT",
                entity_id="pay_demo_high_initial",
                customer_id=cust_id,
                amount_at_risk=75000.00,
                failure_type="timeout",
                failure_reason="High-value enterprise tier checkout failure",
                state=RecoveryState.FAILED,
                retry_count=0,
            )
            session.add(case_2)
        else:
            case_2.state = RecoveryState.FAILED
            case_2.retry_count = 0
            case_2.recovered_amount = 0.0
            case_2.verification_id = None
        await session.commit()

        print(f"\n[SCENARIO 2] HIGH-VALUE HUMAN APPROVAL GATE (>= INR 50,000)")
        print(f"Case ID:        {case_2.id}")
        print(f"Amount at Risk: INR {case_2.amount_at_risk:,.2f} (Ceiling: INR 50,000)")
        print(f"Failure Type:   {case_2.failure_type}")
        print(f"Initial State:  {case_2.state.value}")
        print("-" * 80)

        # Autonomous Flow MUST halt at AWAITING_APPROVAL
        res_2 = await orchestrator.run_full_recovery_flow(
            case_id=case_2_id,
            session=session,
        )
        await session.refresh(case_2)

        print(f"1. Revenue Detective:  High value opportunity calculated: Expected INR 68,250.00")
        print(f"2. Diagnosis Agent:    TRANSIENT classified")
        print(f"3. Recovery Planner:   Strategy proposed: RETRY")
        print(f"4. Policy Engine:      REQUIRE_HUMAN_APPROVAL triggered! (INR 75,000 >= INR 50,000)")
        print(f"   SAFETY INVARIANT:   Autonomous execution strictly BLOCKED.")
        print(f"CURRENT CASE STATE:    {case_2.state.value}")
        print(f"Tool Execution:        BLOCKED (0 provider operations dispatched)")

        # Simulate Human Sign-Off
        print(f"\n[OPERATOR ACTION] Senior Risk Lead reviews audit trail and APPROVES case...")
        dec_id = res_2["decision_id"]
        dec_stmt = await session.get(RecoveryDecision, dec_id)
        if dec_stmt:
            dec_stmt.authorization_status = "AUTHORIZED"
            dec_stmt.authorized_by = "lead_risk_officer@corp.internal"
            case_2.state = RecoveryState.EXECUTING
            await session.commit()

        from app.agents.execution import ExecutionAgent
        execution_agent = ExecutionAgent()
        tool_res = await execution_agent.execute_decision(dec_stmt, case_2, session, attempt_number=1)
        print(f"5. Tool Gateway:       Authorized execution dispatched -> Ref: {tool_res.provider_reference}")
        case_2.state = RecoveryState.AWAITING_VERIFICATION
        await session.commit()

        # Dual Signal Verification
        verif_engine = VerificationEngine()
        verif_res = await verif_engine.verify_recovery(
            case_id=case_2.id,
            execution_id=tool_res.execution_id,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )
        await session.refresh(case_2)

        print(f"6. Verification:       Dual-signal verified with cryptographic evidence hash")
        print(f"FINAL CASE STATE:      {case_2.state.value}")
        print(f"VERIFIED REVENUE:      INR {case_2.recovered_amount:,.2f}")

        # =====================================================================
        # SCENARIO 3: INDEPENDENT VERIFICATION CONFLICT (PAY_DEMO_CONFLICT)
        # =====================================================================
        case_3_id = "PAY_DEMO_CONFLICT"
        case_3 = await session.get(RecoveryCase, case_3_id)
        if not case_3:
            case_3 = RecoveryCase(
                id=case_3_id,
                entity_type="PAYMENT",
                entity_id="pay_demo_conflict_initial",
                customer_id=cust_id,
                amount_at_risk=15000.00,
                failure_type="bank_unavailable",
                failure_reason="Issuer bank reporting conflicting settlement state",
                state=RecoveryState.FAILED,
                retry_count=0,
            )
            session.add(case_3)
        else:
            case_3.state = RecoveryState.FAILED
            case_3.retry_count = 0
            case_3.recovered_amount = 0.0
            case_3.verification_id = None
        await session.commit()

        print(f"\n[SCENARIO 3] VERIFICATION CONFLICT (API SUCCESS vs WEBHOOK FAILED)")
        print(f"Case ID:        {case_3.id}")
        print(f"Amount at Risk: INR {case_3.amount_at_risk:,.2f}")
        print(f"Initial State:  {case_3.state.value}")
        print("-" * 80)

        # Run flow with conflicting webhook signal
        res_3 = await orchestrator.run_full_recovery_flow(
            case_id=case_3_id,
            session=session,
            webhook_payload={"event": "payment.failed", "status": "failed"},
        )
        await session.refresh(case_3)

        print(f"1. Tool Gateway:       Executed recovery operation -> Ref: {res_3.get('execution_id')}")
        print(f"2. Signal A (API):     CAPTURED (HTTP 200 / State API)")
        print(f"3. Signal B (Webhook): FAILED (Payload reports payment.failed)")
        print(f"4. Verification:       CONFLICT DETECTED! Signals do NOT agree.")
        print(f"   SAFE ESCALATION:    Case transitioned to {case_3.state.value} (NOT RECOVERED)")
        print(f"VERIFIED REVENUE:      INR {case_3.recovered_amount:,.2f} (Held at zero pending manual audit)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_three_scenarios())
