import pytest
from app.simulator.generator import SyntheticDataGenerator
from app.simulator.engine import SimulatorEngine


def test_deterministic_generation():
    gen1 = SyntheticDataGenerator(seed=42)
    data1 = gen1.generate_dataset(total_events=200)

    gen2 = SyntheticDataGenerator(seed=42)
    data2 = gen2.generate_dataset(total_events=200)

    assert len(data1["payments"]) == len(data2["payments"])
    assert data1["payments"][0]["id"] == data2["payments"][0]["id"]
    assert data1["payments"][0]["amount"] == data2["payments"][0]["amount"]


def test_ground_truth_integrity():
    gen = SyntheticDataGenerator(seed=100)
    data = gen.generate_dataset(total_events=1000)

    cases = data["recovery_cases"]
    ground_truth = data["ground_truth"]

    assert len(cases) > 0
    assert len(cases) == len(ground_truth)

    # Every ground truth must have binary recoverable flag and best_action
    for gt in ground_truth:
        assert gt["recoverable"] in (0, 1)
        assert gt["best_action"] in [
            "RETRY",
            "PAYMENT_LINK",
            "SUBSCRIPTION_RECOVERY",
            "CUSTOMER_NOTIFICATION",
            "NO_ACTION",
            "HUMAN_REVIEW",
        ]


def test_simulator_economic_lift():
    engine = SimulatorEngine(seed=42)
    result = engine.run_simulation(count=200, scenario_filter="mixed")

    assert result.sample_size == 200
    assert result.revenue_at_risk > 0
    assert result.ray_revenue_recovered >= 0
    # RAY risk-aware recovery should have equal or higher recovery with fewer false interventions
    assert result.ray_false_interventions <= result.baseline_false_interventions
