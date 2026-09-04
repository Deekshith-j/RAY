"""Pytest configuration and session fixtures for RAY test suite."""

import pytest
from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Ensure all database tables and column migrations are applied before tests run."""
    await init_db()
