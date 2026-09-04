from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class OverviewKPIs(BaseModel):
    # Primary KPI
    revenue_recovered: float

    # Secondary KPIs
    revenue_at_risk: float
    estimated_recoverable_revenue: float
    recovery_rate_pct: float  # (revenue_recovered / revenue_at_risk) * 100
    recoverable_capture_rate_pct: float  # (revenue_recovered / estimated_recoverable_revenue) * 100
    
    total_cases: int
    active_cases: int
    recovered_cases: int
    failed_cases: int
    escalated_cases: int

    successful_intervention_rate_pct: float
    false_intervention_rate_pct: float
    average_recovery_time_minutes: float
    human_escalation_rate_pct: float
    verification_success_rate_pct: float
    agent_success_rate_pct: float


class TimeSeriesPoint(BaseModel):
    timestamp: str
    revenue_at_risk: float
    revenue_recovered: float


class DistributionItem(BaseModel):
    name: str
    count: int
    amount: float


class AnalyticsData(BaseModel):
    kpis: OverviewKPIs
    time_series: List[TimeSeriesPoint]
    failure_type_distribution: List[DistributionItem]
    action_distribution: List[DistributionItem]
    state_distribution: Dict[str, int]
