from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db, async_session_factory
from app.simulator.engine import simulator_engine, SimulationResult
from app.simulator.generator import SyntheticDataGenerator
from app.models.entities import (
    Customer,
    Order,
    Payment,
    PaymentAttempt,
    Subscription,
    RecoveryCase,
    AuditLog,
    WebhookEvent,
    RecoveryState,
    RecoveryStrategy,
)

router = APIRouter(prefix="/simulator", tags=["Failure Simulator"])


class RunSimulationRequest(BaseModel):
    count: int = 500
    scenario: str = "mixed"
    seed: Optional[int] = 42


class SeedDbRequest(BaseModel):
    total_events: int = 5000  # Default fast batch for instant UI interactivity
    seed: Optional[int] = 42


@router.post("/run", response_model=SimulationResult)
async def run_simulation(payload: RunSimulationRequest):
    """
    Run an in-memory or Monte Carlo deterministic revenue failure simulation.
    Compares Baseline (always retry once) vs RAY (autonomous risk-aware policy).
    """
    result = simulator_engine.run_simulation(
        count=payload.count,
        scenario_filter=payload.scenario,
        seed=payload.seed,
    )
    return result


async def seed_database_task(total_events: int, seed: int):
    """Background task to populate database with synthetic data."""
    generator = SyntheticDataGenerator(seed=seed)
    dataset = generator.generate_dataset(total_events=total_events)

    async with async_session_factory() as db:
        # Clear existing demo data
        await db.execute(delete(AuditLog))
        await db.execute(delete(RecoveryCase))
        await db.execute(delete(PaymentAttempt))
        await db.execute(delete(Payment))
        await db.execute(delete(Subscription))
        await db.execute(delete(Order))
        await db.execute(delete(Customer))
        await db.execute(delete(WebhookEvent))
        await db.commit()

        # Batch insert customers
        for c in dataset["customers"]:
            db.add(Customer(**c))
        await db.commit()

        # Batch insert orders
        for o in dataset["orders"][:10000]:
            db.add(Order(**o))
        await db.commit()

        # Batch insert payments
        for p in dataset["payments"][:10000]:
            db.add(Payment(**p))
        await db.commit()

        # Batch insert subscriptions
        for s in dataset["subscriptions"]:
            db.add(Subscription(**s))
        await db.commit()

        # Batch insert recovery cases with initial state and some verified recoveries
        for rc in dataset["recovery_cases"][:1500]:
            # Convert string strategy to enum if applicable
            strat = None
            if rc["recommended_action"]:
                try:
                    strat = RecoveryStrategy(rc["recommended_action"])
                except ValueError:
                    strat = RecoveryStrategy.NO_ACTION

            case_obj = RecoveryCase(
                id=rc["id"],
                entity_type=rc["entity_type"],
                entity_id=rc["entity_id"],
                customer_id=rc["customer_id"],
                amount_at_risk=rc["amount_at_risk"],
                recoverability_score=rc["recoverability_score"],
                expected_recovery_value=rc["expected_recovery_value"],
                recovered_amount=0.0,
                failure_reason=rc["failure_reason"],
                failure_type=rc["failure_type"],
                state=RecoveryState.ANALYZING if rc["amount_at_risk"] < 50000 else RecoveryState.AWAITING_APPROVAL,
                recommended_action=strat,
                retry_count=0,
                ai_diagnosis=rc["ai_diagnosis"],
                ai_confidence=rc["ai_confidence"],
                created_at=rc["created_at"],
                updated_at=rc["updated_at"],
            )
            db.add(case_obj)
        await db.commit()

        # Insert some initial audit logs for rich UI demonstration
        cases_res = await db.execute(select(RecoveryCase).limit(20))
        cases = cases_res.scalars().all()
        for c in cases:
            db.add(AuditLog(
                action_id=f"act_{c.id[:8]}_1",
                case_id=c.id,
                agent="Revenue Detective",
                action="DETECT_REVENUE_AT_RISK",
                reason=f"Detected revenue loss on {c.entity_type} {c.entity_id}",
                evidence={"amount": c.amount_at_risk, "failure_type": c.failure_type},
                confidence=0.96,
                policy_result="PASSED",
            ))
            db.add(AuditLog(
                action_id=f"act_{c.id[:8]}_2",
                case_id=c.id,
                agent="Diagnosis Agent",
                action="DIAGNOSE_FAILURE",
                reason=c.ai_diagnosis or "Analyzed failure telemetry",
                evidence={"failure_reason": c.failure_reason},
                confidence=c.ai_confidence or 0.88,
                policy_result="PASSED",
            ))
            if c.state == RecoveryState.AWAITING_APPROVAL:
                db.add(AuditLog(
                    action_id=f"act_{c.id[:8]}_3",
                    case_id=c.id,
                    agent="Policy Engine",
                    action="REQUIRE_HUMAN_APPROVAL",
                    reason=f"Amount ₹{c.amount_at_risk:,.2f} exceeds threshold of ₹50,000. Paused for human authorization.",
                    approval_required=True,
                    policy_result="APPROVAL_REQUIRED",
                ))
        await db.commit()


@router.post("/seed-db")
async def seed_database(
    payload: SeedDbRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Seed the database with synthetic payments and recovery cases for demo."""
    # Run in foreground for fast response if count is reasonable
    await seed_database_task(payload.total_events, payload.seed or 42)
    return {
        "status": "success",
        "message": f"Database successfully seeded with synthetic events (seed={payload.seed or 42}).",
    }
