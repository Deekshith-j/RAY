import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    APP_NAME: str = "RAY — Autonomous Revenue Recovery & Verification Engine"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Canonical Database Path
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent.as_posix()}/ray.db"
    )
    ECHO_SQL: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Razorpay Test Mode & Demo Flags
    RAZORPAY_TEST_MODE: bool = True  # Safety: True for Test Mode/Mock, False blocks non-prod execution
    DEMO_MODE: bool = True           # Controls demo reset endpoints and pre-seeded accounts
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "rzp_secret_placeholder"
    RAZORPAY_WEBHOOK_SECRET: str = "webhook_secret_placeholder"

    # Deterministic Policy Defaults
    MAX_RETRY_ATTEMPTS: int = 1
    AUTO_RETRY_ENABLED: bool = True
    AUTO_RETRY_MAX_AMOUNT: float = 25000.0  # Max ₹25,000 for automatic retry (covers ₹24,999 demo)
    ALLOWED_RETRY_FAILURE_TYPES: List[str] = Field(
        default_factory=lambda: ["timeout", "network_error", "temporary_failure", "bank_unavailable"]
    )
    PAYMENT_LINK_ENABLED: bool = True
    PAYMENT_LINK_MAX_AMOUNT: float = 50000.0  # Max ₹50,000 for automated payment link
    HUMAN_APPROVAL_THRESHOLD: float = 50000.0  # ₹50,000+ requires human approval
    MAX_TOTAL_RECOVERY_ATTEMPTS: int = 2

    # LLM & Multi-Agent Architecture
    LLM_PROVIDER: str = "mock"  # "mock" or "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MAX_AGENT_STEPS: int = 12
    MODEL_VERSION: str = "ray-recov-v1-production"
    FEATURE_SCHEMA_VERSION: str = "v1.0"


settings = Settings()

