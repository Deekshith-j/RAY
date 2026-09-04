"""Agent 3 — Recovery Planner: Synthesizes ML probabilities, diagnoses, and policy constraints to propose a strategy."""

from typing import List
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.agents.provider import get_llm_provider
from app.agents.detective import RevenueOpportunity
from app.agents.diagnosis import DiagnosisOutput


class RecoveryPlanOutput(BaseModel):
    """Structured candidate recovery strategy proposed by Recovery Planner."""

    recommended_strategy: str = Field(
        ...,
        description="One of: RETRY, PAYMENT_LINK, SUBSCRIPTION_RECOVERY, CUSTOMER_NOTIFICATION, NO_ACTION, HUMAN_REVIEW",
    )
    rationale: str = Field(..., description="Operational rationale based on expected value and risk")
    expected_recovery: str = Field(..., description="Monetary INR expected recovery")
    alternatives: List[str] = Field(default_factory=list, description="Alternative recovery strategies considered")


class RecoveryPlanner(BaseAgent):
    """
    Agent 3: Proposes the candidate recovery strategy.
    Proposes only; DOES NOT authorize.
    """

    def __init__(self):
        super().__init__(name="RecoveryPlanner")
        self.llm = get_llm_provider()

    async def plan_recovery(
        self,
        opportunity: RevenueOpportunity,
        diagnosis: DiagnosisOutput,
    ) -> RecoveryPlanOutput:
        self.increment_step()

        system_prompt = (
            "You are RAY's Recovery Planner. Formulate candidate recovery strategies strictly from:\n"
            "RETRY, PAYMENT_LINK, SUBSCRIPTION_RECOVERY, CUSTOMER_NOTIFICATION, NO_ACTION, HUMAN_REVIEW.\n"
            "Consider ML probability, Expected Recovery Value, failure family, and customer history.\n"
            "You only propose; the deterministic Policy Engine makes the final authorization decision."
        )

        user_prompt = (
            f"Case: {opportunity.case_id}\n"
            f"Amount: INR {opportunity.amount}\n"
            f"Expected Recovery: INR {opportunity.expected_recovery}\n"
            f"Estimated Recovery Probability: {opportunity.recoverability_probability:.4f} ({opportunity.recoverability_band})\n"
            f"Diagnosis: {diagnosis.diagnosis} ({diagnosis.confidence * 100:.1f}% confidence)\n"
            f"Diagnosis Family: {diagnosis.recommended_recovery_family}\n"
            f"Diagnosis Evidence: {diagnosis.evidence}\n"
            "Propose the optimal recovery strategy and alternatives."
        )

        return await self.llm.structured_generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            schema=RecoveryPlanOutput,
        )
