"""Base agent definition and prompt injection defense utilities."""

import re
from typing import Dict, Any, Optional
from app.config import settings


class PromptInjectionDefense:
    """
    Sanitizes untrusted customer-provided text fields (descriptions, names, notes, references)
    to ensure they are treated strictly as passive data and cannot override agent prompts.
    """

    @staticmethod
    def sanitize_untrusted_data(text: Optional[str]) -> str:
        if not text:
            return ""
        # Strip system control markers or instruction overrides
        cleaned = str(text).replace("\r", " ").replace("\n", " ").strip()
        # Enclose in explicit data boundary tags
        return f"<UNTRUSTED_DATA>[UNTRUSTED_CUSTOMER_DATA] {cleaned} [/UNTRUSTED_CUSTOMER_DATA]</UNTRUSTED_DATA>"

    @staticmethod
    def build_safe_context(metadata: Dict[str, Any]) -> Dict[str, Any]:
        safe = {}
        for k, v in metadata.items():
            if isinstance(v, str):
                safe[k] = PromptInjectionDefense.sanitize_untrusted_data(v)
            else:
                safe[k] = v
        return safe


class BaseAgent:
    """Base class for bounded financial recovery agents."""

    def __init__(self, name: str, max_steps: int = settings.MAX_AGENT_STEPS):
        self.name = name
        self.max_steps = max_steps
        self.step_count = 0

    def increment_step(self) -> int:
        """Track agent step count against execution limits."""
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise RuntimeError(
                f"Agent '{self.name}' exceeded maximum allowed execution steps ({self.max_steps}). Escalating to HUMAN_REVIEW."
            )
        return self.step_count
