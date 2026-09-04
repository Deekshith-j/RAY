"""LLM Provider abstraction supporting Mock (offline deterministic) and Ollama."""

from typing import Protocol, Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
import httpx
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    """Protocol for LLM reasoning providers with structured output enforcement."""

    async def structured_generate(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output adhering to a Pydantic schema."""
        ...


class MockLLMProvider:
    """
    Deterministic offline LLM provider.
    Inspects prompt content and generates exact structured Pydantic objects.
    No API keys, external calls, or non-deterministic latency.
    """

    async def structured_generate(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: float = 0.0,
    ) -> T:
        schema_name = schema.__name__

        # 1. Diagnosis Agent Output Mock
        if schema_name == "DiagnosisOutput":
            prompt_lower = prompt.lower()
            if "timeout" in prompt_lower or "network_error" in prompt_lower or "bank_unavailable" in prompt_lower:
                return schema(
                    diagnosis="TRANSIENT_FAILURE",
                    evidence=["Gateway timeout recorded", "Customer exhibits high historical success", "Zero opt-out flags"],
                    confidence=0.92,
                    recommended_recovery_family="RETRY",
                )
            elif "card_expired" in prompt_lower or "subscription" in prompt_lower:
                return schema(
                    diagnosis="SUBSCRIPTION_EXPIRED",
                    evidence=["Card expiration code reported by issuer", "Active recurring subscription"],
                    confidence=0.88,
                    recommended_recovery_family="SUBSCRIPTION_RECOVERY",
                )
            elif "abandonment" in prompt_lower or "insufficient" in prompt_lower:
                return schema(
                    diagnosis="ABANDONMENT",
                    evidence=["Checkout drop-off detected", "Customer initiated payment flow"],
                    confidence=0.85,
                    recommended_recovery_family="PAYMENT_LINK",
                )
            else:
                return schema(
                    diagnosis="UNKNOWN",
                    evidence=["Unclassified payment gateway error"],
                    confidence=0.40,
                    recommended_recovery_family="HUMAN_REVIEW",
                )

        # 2. Recovery Planner Output Mock
        elif schema_name == "RecoveryPlanOutput":
            prompt_lower = prompt.lower()
            if "transient" in prompt_lower or "retry" in prompt_lower:
                return schema(
                    recommended_strategy="RETRY",
                    rationale="High recoverability probability and transient timeout. Auto-retry within safe limit.",
                    expected_recovery="22939.18",
                    alternatives=["PAYMENT_LINK", "CUSTOMER_NOTIFICATION"],
                )
            elif "subscription" in prompt_lower:
                return schema(
                    recommended_strategy="SUBSCRIPTION_RECOVERY",
                    rationale="Card update link needed for expired recurring subscription.",
                    expected_recovery="1999.00",
                    alternatives=["PAYMENT_LINK"],
                )
            elif "abandonment" in prompt_lower:
                return schema(
                    recommended_strategy="PAYMENT_LINK",
                    rationale="Checkout abandonment recovery via branded Razorpay payment link.",
                    expected_recovery="4999.00",
                    alternatives=["CUSTOMER_NOTIFICATION"],
                )
            else:
                return schema(
                    recommended_strategy="HUMAN_REVIEW",
                    rationale="Uncertain failure pattern requires financial operator intervention.",
                    expected_recovery="0.00",
                    alternatives=["NO_ACTION"],
                )

        # Fallback default instantiation
        try:
            return schema()
        except Exception:
            raise ValueError(f"MockLLMProvider does not support schema '{schema_name}'")


class OllamaLLMProvider:
    """Local Ollama instance communicating over HTTP."""

    def __init__(self, base_url: Optional[str] = None, model: str = "llama3"):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model

    async def structured_generate(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: float = 0.0,
    ) -> T:
        format_schema = schema.model_json_schema()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": f"{system_prompt}\nReturn JSON strictly matching schema: {format_schema}"},
                        {"role": "user", "content": prompt},
                    ],
                    "format": "json",
                    "options": {"temperature": temperature},
                    "stream": False,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["message"]["content"]
            return schema.model_validate_json(raw_text)


def get_llm_provider() -> LLMProvider:
    """Factory returning configured LLM provider based on settings."""
    if settings.LLM_PROVIDER.lower() == "ollama":
        return OllamaLLMProvider()
    return MockLLMProvider()
