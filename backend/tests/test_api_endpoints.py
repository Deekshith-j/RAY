import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest.mark.asyncio
async def test_health_endpoint():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "RAY" in data["app"]


@pytest.mark.asyncio
async def test_analytics_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "revenue_recovered" in data
        assert "revenue_at_risk" in data


@pytest.mark.asyncio
async def test_simulator_run_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"count": 50, "scenario": "mixed", "seed": 42}
        response = await client.post("/api/v1/simulator/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["sample_size"] == 50
        assert "ray_revenue_recovered" in data
        assert "baseline_revenue_recovered" in data
