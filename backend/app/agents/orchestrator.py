"""Deterministic Agent Orchestrator linking the bounded multi-agent recovery lifecycle."""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import (
    RecoveryCase,
    RecoveryDecision,
    RecoveryState,
    AuditLog,
    RecoveryStrategy,
)
from app.agents.detective import RevenueDetective, RevenueOpportunity
from app.agents.diagnosis import DiagnosisAgent, DiagnosisOutput
from app.agents.planner import RecoveryPlanner, RecoveryPlanOutput
from app.agents.execution import ExecutionAgent
from app.core.policy_engine import PolicyEngine
from app.verification.engine import VerificationEngine
from app.verification.models import VerificationResult, VerificationStatus
from app.tools.schemas import ToolCallResult


class RecoveryTimelineEvent:
    def __init__(
        self,
        event_id: str,
        case_id: str,
        event_type: str,
        actor: str,
        details: Dict[str, Any],
        correlation_id: str,
        timestamp: Optional[datetime] = None,
    ):
        self.event_id = event_id
        self.case_id = case_id
        self.event_type = event_type
        self.actor = actor
        self.details = details
        self.correlation_id = correlation_id
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentOrchestrator:
    """
    Coordinates the 5 bounded recovery agents, Policy Engine, and Verification Engine.
    Enforces maximum step limits and deterministic financial authority.
    """

    def __init__(self):
        self.detective = RevenueDetective()
        self.diagnosis_agent = DiagnosisAgent()
        self.planner = RecoveryPlanner()
        self.execution_agent = ExecutionAgent()
        self.policy_engine = PolicyEngine()
        self.verification_engine = VerificationEngine()
        self._timeline_events: Dict[str, List[RecoveryTimelineEvent]] = {}

    def _emit_event(
        self,
        case_id: str,
        event_type: str,
        actor: str,
        details: Dict[str, Any],
        correlation_id: str,
    ) -> RecoveryTimelineEvent:
        evt = RecoveryTimelineEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            details=details,
            correlation_id=correlation_id,
        )
        if case_id not in self._timeline_events:
            self._timeline_events[case_id] = []
        self._timeline_events[case_id].append(evt)
        return evt

    def get_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._timeline_events.get(case_id, [])]

    async def run_full_recovery_flow(
        self,
        case_id: str,
        session: AsyncSession,
        webhook_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete bounded recovery cycle:
        Case -> Detective -> Diagnosis -> Planner -> Policy -> Execution -> Verification
        """
        correlation_id = f"RAY-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # 1. Fetch Case
        stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
        res = await session.execute(stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise ValueError(f"Case '{case_id}' does not exist")

        self._emit_event(case_id, "ANALYSIS_STARTED", "AgentOrchestrator", {"state": case.state.value}, correlation_id)

        try:
            # 2. Step 1: Revenue Detective
            opportunity = await self.detective.analyze_opportunity(case_id, session, correlation_id=correlation_id)
            self._emit_event(
                case_id,
                "ML_PREDICTION",
                "RevenueDetective",
                {
                    "probability": opportunity.recoverability_probability,
                    "expected_recovery": str(opportunity.expected_recovery),
                    "band": opportunity.recoverability_band,
                },
                correlation_id,
            )

            # 3. Step 2: Diagnosis Agent
            diagnosis = await self.diagnosis_agent.diagnose(opportunity)
            self._emit_event(
                case_id,
                "DIAGNOSIS_COMPLETE",
                "DiagnosisAgent",
                {
                    "diagnosis": diagnosis.diagnosis,
                    "confidence": diagnosis.confidence,
                    "evidence": diagnosis.evidence,
                    "family": diagnosis.recommended_recovery_family,
                },
                correlation_id,
            )

            # 4. Step 3: Recovery Planner
            plan = await self.planner.plan_recovery(opportunity, diagnosis)
            valid_strategies = [s.value for s in RecoveryStrategy]
            if plan.recommended_strategy not in valid_strategies:
                raise ValueError(f"Recovery Planner proposed unsupported or hallucinated strategy: '{plan.recommended_strategy}'")

            self._emit_event(
                case_id,
                "RECOVERY_PLAN_CREATED",
                "RecoveryPlanner",
                {
                    "recommended_strategy": plan.recommended_strategy,
                    "rationale": plan.rationale,
                    "expected_recovery": plan.expected_recovery,
                },
                correlation_id,
            )

        except Exception as agent_err:
            case.state = RecoveryState.HUMAN_REVIEW
            audit = AuditLog(
                action_id=f"act_{uuid.uuid4().hex[:12]}",
                case_id=case_id,
                agent="AgentOrchestrator",
                action="LLM_FAILURE_ESCALATION",
                reason=f"Agent failure/timeout: {str(agent_err)}. Escalated to HUMAN_REVIEW.",
                policy_result="STOPPED",
                execution_result="FAILED",
                timestamp=datetime.utcnow(),
            )
            session.add(audit)
            await session.commit()
            self._emit_event(
                case_id,
                "LLM_FAILURE_STOP",
                "AgentOrchestrator",
                {"error": str(agent_err), "escalation": "HUMAN_REVIEW"},
                correlation_id,
            )
            return {
                "case_id": case_id,
                "case_state": RecoveryState.HUMAN_REVIEW.value,
                "error": str(agent_err),
                "timeline": self.get_timeline(case_id),
            }

        # 5. Step 4: Policy Engine Check (DETERMINISTIC AUTHORITY)
        self._emit_event(case_id, "POLICY_CHECK_STARTED", "PolicyEngine", {"strategy": plan.recommended_strategy}, correlation_id)
        strat_enum = RecoveryStrategy(plan.recommended_strategy)
        policy_eval = self.policy_engine.evaluate(case, strat_enum)

        decision_id = f"dec_{uuid.uuid4().hex[:16]}"
        is_high_value_escalation = policy_eval.requires_human_approval
        auth_status = "PENDING" if is_high_value_escalation else ("AUTHORIZED" if policy_eval.allowed else "REJECTED")

        # Persist RecoveryDecision
        decision = RecoveryDecision(
            id=decision_id,
            case_id=case_id,
            recommended_strategy=plan.recommended_strategy,
            probability_of_recovery=opportunity.recoverability_probability,
            expected_recovery=float(opportunity.expected_recovery),
            rationale=plan.rationale,
            policy_result="REQUIRE_HUMAN_APPROVAL" if is_high_value_escalation else ("ALLOW" if policy_eval.allowed else "DENY"),
            policy_version="v1.0",
            authorization_required=is_high_value_escalation,
            authorization_status=auth_status,
            correlation_id=correlation_id,
            created_at=datetime.utcnow(),
        )
        session.add(decision)
        await session.commit()

        if is_high_value_escalation:
            case.state = RecoveryState.AWAITING_APPROVAL
            await session.commit()
            self._emit_event(case_id, "HUMAN_APPROVAL_REQUIRED", "PolicyEngine", {"amount": float(case.amount_at_risk)}, correlation_id)
            return {
                "case_id": case_id,
                "status": "AWAITING_APPROVAL",
                "decision_id": decision_id,
                "authorization_required": True,
                "opportunity": opportunity.model_dump(),
                "diagnosis": diagnosis.model_dump(),
                "plan": plan.model_dump(),
                "timeline": self.get_timeline(case_id),
            }

        if not policy_eval.allowed:
            case.state = RecoveryState.STOPPED
            await session.commit()
            self._emit_event(case_id, "POLICY_DENIED", "PolicyEngine", {"reason": policy_eval.reason}, correlation_id)
            return {
                "case_id": case_id,
                "status": "STOPPED",
                "decision_id": decision_id,
                "policy_eval": {"allowed": False, "reason": policy_eval.reason},
                "timeline": self.get_timeline(case_id),
            }

        self._emit_event(case_id, "POLICY_ALLOWED", "PolicyEngine", {"rule": policy_eval.rule_code}, correlation_id)

        # 6. Step 5: Execution via Tool Gateway
        case.state = RecoveryState.EXECUTING
        await session.commit()
        self._emit_event(case_id, "TOOL_CALL_STARTED", "ExecutionAgent", {"operation": plan.recommended_strategy}, correlation_id)

        tool_result: ToolCallResult = await self.execution_agent.execute_decision(
            decision=decision,
            case=case,
            session=session,
            attempt_number=case.retry_count + 1,
        )

        if tool_result.status != "SUCCESS":
            case.state = RecoveryState.FAILED
            await session.commit()
            self._emit_event(case_id, "TOOL_CALL_FAILED", "ToolGateway", {"reason": tool_result.rejection_reason}, correlation_id)
            return {
                "case_id": case_id,
                "status": "EXECUTION_FAILED",
                "decision_id": decision_id,
                "tool_result": tool_result.model_dump(),
                "timeline": self.get_timeline(case_id),
            }

        self._emit_event(case_id, "TOOL_CALL_COMPLETED", "ToolGateway", {"provider_ref": tool_result.provider_reference}, correlation_id)
        case.state = RecoveryState.AWAITING_VERIFICATION
        await session.commit()

        # 7. Step 6: Dual-Signal Verification
        self._emit_event(case_id, "VERIFICATION_STARTED", "VerificationEngine", {"execution_id": tool_result.execution_id}, correlation_id)
        verif_result: VerificationResult = await self.verification_engine.verify_recovery(
            case_id=case_id,
            execution_id=tool_result.execution_id,
            session=session,
            webhook_payload=webhook_payload,
        )

        if verif_result.status == VerificationStatus.VERIFIED:
            self._emit_event(case_id, "RECOVERY_VERIFIED", "VerificationEngine", {"verified_amount": verif_result.verified_amount}, correlation_id)
        else:
            self._emit_event(case_id, f"VERIFICATION_{verif_result.status.value}", "VerificationEngine", {}, correlation_id)

        return {
            "case_id": case_id,
            "status": case.state.value,
            "decision_id": decision_id,
            "execution_id": tool_result.execution_id,
            "verification_id": verif_result.verification_id,
            "verified_amount": verif_result.verified_amount,
            "evidence_hash": verif_result.evidence_hash,
            "timeline": self.get_timeline(case_id),
        }


orchestrator = AgentOrchestrator()
