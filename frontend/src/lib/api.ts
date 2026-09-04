const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface OverviewKPIs {
  revenue_recovered: number;
  revenue_at_risk: number;
  estimated_recoverable_revenue: number;
  recovery_rate_pct: number;
  recoverable_capture_rate_pct: number;
  total_cases: number;
  active_cases: number;
  recovered_cases: number;
  failed_cases: number;
  escalated_cases: number;
  successful_intervention_rate_pct: number;
  false_intervention_rate_pct: number;
  average_recovery_time_minutes: number;
  human_escalation_rate_pct: number;
  verification_success_rate_pct: number;
  agent_success_rate_pct: number;
}

export interface RecoveryCase {
  id: string;
  entity_type: string;
  entity_id: string;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  amount_at_risk: number;
  recoverability_score: number;
  expected_recovery_value: number;
  recovered_amount: number;
  failure_reason: string;
  failure_type: string;
  state: string;
  recommended_action?: string;
  authorized_action?: string;
  executed_action?: string;
  retry_count: number;
  ai_diagnosis?: string;
  ai_confidence?: number;
  human_approved?: boolean;
  human_approved_by?: string;
  created_at: string;
  updated_at: string;
}

export interface SimulationResult {
  scenario: string;
  sample_size: number;
  revenue_at_risk: number;
  estimated_recoverable_revenue: number;
  baseline_actions_attempted: number;
  baseline_successful_recoveries: number;
  baseline_revenue_recovered: number;
  baseline_recovery_rate_pct: number;
  baseline_false_interventions: number;
  ray_actions_attempted: number;
  ray_successful_recoveries: number;
  ray_revenue_recovered: number;
  ray_recovery_rate_pct: number;
  ray_false_interventions: number;
  ray_human_escalations: number;
  ray_verification_rate_pct: number;
  lift_revenue_recovered: number;
  lift_percentage: number;
  cases: any[];
}

export async function fetchOverviewKPIs(): Promise<OverviewKPIs> {
  const res = await fetch(`${API_BASE}/api/v1/analytics/overview`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to fetch overview KPIs");
  }
  return res.json();
}

export async function fetchCases(params: {
  state?: string;
  failure_type?: string;
  limit?: number;
} = {}): Promise<RecoveryCase[]> {
  const search = new URLSearchParams();
  if (params.state) search.set("state", params.state);
  if (params.failure_type) search.set("failure_type", params.failure_type);
  if (params.limit) search.set("limit", params.limit.toString());

  const res = await fetch(`${API_BASE}/api/v1/cases?${search.toString()}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Failed to fetch cases");
  }
  return res.json();
}

export async function runSimulation(count: number = 500, scenario: string = "mixed"): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/api/v1/simulator/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ count, scenario, seed: 42 }),
  });
  if (!res.ok) {
    throw new Error("Failed to run simulation");
  }
  return res.json();
}

export async function seedDatabase(totalEvents: number = 5000): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/simulator/seed-db`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ total_events: totalEvents, seed: 42 }),
  });
  if (!res.ok) {
    throw new Error("Failed to seed database");
  }
  return res.json();
}

export interface MLModelMetrics {
  model_version: string;
  model_type: string;
  is_calibrated: boolean;
  calibration_method: string;
  validation_metrics: {
    pr_auc: number;
    roc_auc: number;
    precision: number;
    recall: number;
    f1: number;
    brier_score: number;
    log_loss: number;
  };
  test_metrics: {
    pr_auc: number;
    roc_auc: number;
    precision: number;
    recall: number;
    f1: number;
    brier_score: number;
    log_loss: number;
  };
}

export async function fetchMLMetrics(): Promise<MLModelMetrics | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/ml/metrics`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchCaseById(id: string): Promise<RecoveryCase | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/cases/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchCaseDecision(caseId: string): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery/${caseId}/decision`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchCaseExecution(caseId: string): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery/${caseId}/execution`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchCaseVerification(caseId: string): Promise<any | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery/${caseId}/verification`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchCaseTimeline(caseId: string): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery/${caseId}/timeline`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return data.events || [];
  } catch {
    return [];
  }
}

export async function runFullRecovery(caseId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/recovery/${caseId}/run-full`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Recovery failed");
  }
  return res.json();
}

export async function resetDemo(): Promise<{ status: string; deleted_demo_cases: number; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/demo/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Reset failed" }));
    throw new Error(err.detail || "Demo reset failed");
  }
  return res.json();
}

