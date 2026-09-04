"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchOverviewKPIs,
  fetchCases,
  runSimulation,
  seedDatabase,
  resetDemo,
  OverviewKPIs,
  RecoveryCase,
  SimulationResult,
} from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  ArrowUpRight,
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCw,
  Clock,
  Sparkles,
  ChevronRight,
  Database,
  Trash2,
  Lock,
  Cpu,
  CheckCircle,
  FileCheck2,
} from "lucide-react";

export default function OverviewPage() {
  const [kpis, setKpis] = useState<OverviewKPIs | null>(null);
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiData, casesData] = await Promise.all([
        fetchOverviewKPIs().catch(() => null),
        fetchCases({ limit: 15 }).catch(() => []),
      ]);
      setKpis(kpiData);
      setCases(casesData);
    } catch (err) {
      console.error("Error loading overview data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunSimulation = async (count: number = 500) => {
    setSimulating(true);
    try {
      const res = await runSimulation(count, "mixed");
      setSimResult(res);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setSimulating(false);
    }
  };

  const handleSeed = async () => {
    setLoading(true);
    try {
      await seedDatabase(5000);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDemo = async () => {
    if (!window.confirm("Reset all demo data and restore initial clean state?")) return;
    setResetting(true);
    try {
      const res = await resetDemo();
      setResetMessage(`Demo reset successful: ${res.deleted_demo_cases} temporary demo records purged.`);
      await loadData();
      setTimeout(() => setResetMessage(null), 5000);
    } catch (e: any) {
      alert("Reset failed: " + (e.message || e));
    } finally {
      setResetting(false);
    }
  };

  // Canonical metric breakdown calculations
  const revenueAtRisk = kpis ? kpis.revenue_at_risk : 0;
  const expectedRecovery = kpis ? kpis.estimated_recoverable_revenue : 0;
  const verifiedRevenue = kpis ? kpis.revenue_recovered : 0;
  const executedAmount = cases.reduce(
    (acc, c) => (["EXECUTING", "AWAITING_VERIFICATION", "RECOVERED"].includes(c.state) ? acc + c.amount_at_risk : acc),
    0
  );

  return (
    <div className="space-y-8">
      {/* Product Positioning & Core Differentiator Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-950/60 via-slate-900 to-indigo-950/50 border border-blue-500/30 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/40">
                Razorpay AI Buildathon 2026
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                AI Revenue Recovery Control Plane
              </span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">
              RAY — Revenue Autonomy Engine
            </h2>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-blue-300 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400 shrink-0" />
                <span>&ldquo;AI reasons about revenue. Deterministic controls control money.&rdquo;</span>
              </p>
              <p className="text-xs text-slate-400">
                RAY never considers revenue recovered until the financial outcome is independently proven via dual-signal API + webhook verification.
              </p>
            </div>
          </div>

          {/* Quick Action Controls */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handleSeed}
              disabled={loading || resetting}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
            >
              <Database className="w-3.5 h-3.5 text-blue-400" />
              Seed 5,000 Events
            </button>
            <button
              onClick={() => handleRunSimulation(500)}
              disabled={simulating || resetting}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 transition disabled:opacity-50"
            >
              {simulating ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              Run 500 Simulation
            </button>
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 text-xs font-semibold border border-rose-800/60 transition disabled:opacity-50"
              title="Reset test demo data"
            >
              {resetting ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
              Reset Demo
            </button>
          </div>
        </div>

        {resetMessage && (
          <div className="mt-4 p-3 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-xs text-emerald-300 font-medium">
            {resetMessage}
          </div>
        )}
      </div>

      {/* AI Safety Boundary Architecture Status Strip */}
      <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-xs space-y-2">
        <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-slate-400 font-bold">
          <span className="flex items-center gap-1.5 text-white">
            <Lock className="w-3.5 h-3.5 text-blue-400" /> AI Safety & Governance Boundary
          </span>
          <span className="text-slate-500">Separation of Concerns: PREDICT &ne; RECOMMEND &ne; AUTHORIZE &ne; EXECUTE &ne; VERIFY</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1 font-mono text-[11px]">
          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-center">
            <p className="text-slate-400 text-[10px]">ML PREDICTION</p>
            <p className="font-bold text-blue-400 mt-0.5">ADVISORY</p>
          </div>
          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-center">
            <p className="text-slate-400 text-[10px]">LLM AGENTS</p>
            <p className="font-bold text-indigo-400 mt-0.5">ADVISORY</p>
          </div>
          <div className="p-2 rounded bg-slate-900/80 border border-emerald-900/60 text-center">
            <p className="text-slate-400 text-[10px]">POLICY ENGINE</p>
            <p className="font-bold text-emerald-400 mt-0.5">AUTHORITATIVE</p>
          </div>
          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-center">
            <p className="text-slate-400 text-[10px]">TOOL GATEWAY</p>
            <p className="font-bold text-amber-400 mt-0.5">ENFORCED</p>
          </div>
          <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-center col-span-2 sm:col-span-1">
            <p className="text-slate-400 text-[10px]">VERIFICATION</p>
            <p className="font-bold text-cyan-400 mt-0.5">INDEPENDENT</p>
          </div>
        </div>
      </div>

      {/* 4 Canonical Metrics: Risk vs Expected vs Executed vs Verified */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400">
            Canonical Financial Metric Separation
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">Guaranteed Decimal Precision (Paise Rounded)</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Revenue at Risk */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg">
            <div className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1">
              Exposure
            </div>
            <p className="text-xs text-slate-400">Revenue at Risk</p>
            <div className="text-2xl font-extrabold text-white mt-2 tracking-tight">
              {formatCurrencyINR(revenueAtRisk)}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Across {kpis ? kpis.total_cases.toLocaleString() : 0} total cases
            </p>
          </div>

          {/* 2. Expected Recovery */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg">
            <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">
              P(Rec) &times; Amount
            </div>
            <p className="text-xs text-slate-400">Expected Recovery</p>
            <div className="text-2xl font-extrabold text-blue-300 mt-2 tracking-tight">
              {formatCurrencyINR(expectedRecovery)}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Capture: {kpis ? formatPercentage(kpis.recoverable_capture_rate_pct) : "0.0%"}
            </p>
          </div>

          {/* 3. Executed Amount */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg">
            <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
              Dispatched
            </div>
            <p className="text-xs text-slate-400">Executed Amount</p>
            <div className="text-2xl font-extrabold text-amber-300 mt-2 tracking-tight">
              {formatCurrencyINR(executedAmount)}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Authorized via ToolGateway
            </p>
          </div>

          {/* 4. Verified Revenue (Canonical) */}
          <div className="p-5 rounded-xl bg-gradient-to-br from-slate-900 to-slate-900/90 border border-emerald-500/40 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between text-xs font-semibold text-emerald-400 mb-1">
              <span className="uppercase tracking-wider">Canonical KPI</span>
              <span className="flex items-center gap-1 text-[10px] bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30">
                <ShieldCheck className="w-3 h-3" /> VERIFIED
              </span>
            </div>
            <p className="text-xs text-slate-400">Verified Revenue</p>
            <div className="text-2xl font-black text-emerald-400 mt-2 tracking-tight">
              {formatCurrencyINR(verifiedRevenue)}
            </div>
            <div className="mt-2 flex items-center gap-2 text-xs text-emerald-400 font-medium">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>{kpis ? formatPercentage(kpis.recovery_rate_pct) : "0.0%"} recovery rate</span>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Guardrails Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-xs">
          <div className="text-slate-400 uppercase tracking-wider font-semibold text-[11px] mb-1">Intervention Precision</div>
          <div className="text-xl font-bold text-white mt-1">
            {kpis ? formatPercentage(kpis.successful_intervention_rate_pct) : "100%"}
          </div>
          <p className="text-slate-500 text-[11px] mt-1">
            False intervention rate: {kpis ? formatPercentage(kpis.false_intervention_rate_pct) : "0%"}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-xs">
          <div className="text-slate-400 uppercase tracking-wider font-semibold text-[11px] mb-1">Human Approval Ceiling</div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            {kpis ? kpis.escalated_cases : 0} Cases Awaiting Approval
          </div>
          <p className="text-slate-500 text-[11px] mt-1">
            Ceiling enforced for high-value transactions (&ge; ₹50,000)
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 text-xs">
          <div className="text-slate-400 uppercase tracking-wider font-semibold text-[11px] mb-1">Dual-Signal Agreement</div>
          <div className="text-xl font-bold text-cyan-400 mt-1">
            {kpis ? formatPercentage(kpis.verification_success_rate_pct) : "100%"}
          </div>
          <p className="text-slate-500 text-[11px] mt-1">
            Razorpay API Polling + Webhook SHA-256 agreement
          </p>
        </div>
      </div>

      {/* Simulation Result Callout (if executed) */}
      {simResult && (
        <div className="p-6 rounded-xl bg-blue-950/40 border border-blue-500/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm">
              <Sparkles className="w-4 h-4" />
              <span>Simulation Benchmark Results ({simResult.sample_size} cases, Scenario: {simResult.scenario})</span>
            </div>
            <span className="text-xs px-2.5 py-1 rounded bg-blue-500/20 text-blue-300 font-bold">
              +{formatCurrencyINR(simResult.lift_revenue_recovered)} Lift ({simResult.lift_percentage}%)
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-slate-400">Baseline Recovered (Naive Retry)</p>
              <p className="text-lg font-bold text-slate-200 mt-1">{formatCurrencyINR(simResult.baseline_revenue_recovered)}</p>
              <p className="text-[11px] text-rose-400 mt-0.5">{simResult.baseline_false_interventions} false interventions</p>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-slate-400">RAY Recovered (Risk-Aware Policy)</p>
              <p className="text-lg font-bold text-emerald-400 mt-1">{formatCurrencyINR(simResult.ray_revenue_recovered)}</p>
              <p className="text-[11px] text-emerald-400 mt-0.5">{simResult.ray_false_interventions} false interventions</p>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-slate-400">Human Escalations</p>
              <p className="text-lg font-bold text-amber-400 mt-1">{simResult.ray_human_escalations}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">High-value (&ge; ₹50,000)</p>
            </div>
            <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800">
              <p className="text-slate-400">Verification Rate</p>
              <p className="text-lg font-bold text-white mt-1">{formatPercentage(simResult.ray_verification_rate_pct)}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">Cryptographically confirmed</p>
            </div>
          </div>
        </div>
      )}

      {/* Recovery Cases Table */}
      <div className="rounded-xl bg-[#0B1120] border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Prioritized Recovery Queue</h3>
            <p className="text-xs text-slate-400">
              Ranked by Expected Recovery Value: Amount at Risk &times; P(Recoverable)
            </p>
          </div>
          <Link
            href="/cases"
            className="flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300 transition"
          >
            View all cases <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Case ID</th>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Amount at Risk</th>
                <th className="px-5 py-3">P(Rec)</th>
                <th className="px-5 py-3">Expected Value</th>
                <th className="px-5 py-3">Failure Reason</th>
                <th className="px-5 py-3">Strategy</th>
                <th className="px-5 py-3">State</th>
                <th className="px-5 py-3">Verified Recovered</th>
                <th className="px-5 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-5 py-8 text-center text-slate-500">
                    No cases loaded yet. Click <strong>Seed 5,000 Events</strong> or <strong>Run Simulation</strong> above!
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3.5 font-mono text-slate-300 font-medium">
                      <Link href={`/cases/${c.id}`} className="hover:underline text-blue-400">
                        {c.id.slice(0, 18)}
                      </Link>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-white">{c.customer_name || c.customer_id}</td>
                    <td className="px-5 py-3.5 font-semibold text-white">{formatCurrencyINR(c.amount_at_risk)}</td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`font-semibold ${
                          c.recoverability_score > 0.7
                            ? "text-emerald-400"
                            : c.recoverability_score > 0.4
                            ? "text-amber-400"
                            : "text-rose-400"
                        }`}
                      >
                        {(c.recoverability_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-blue-400">
                      {formatCurrencyINR(c.expected_recovery_value)}
                    </td>
                    <td className="px-5 py-3.5 max-w-xs truncate text-slate-400" title={c.failure_reason}>
                      {c.failure_reason}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-200 border border-slate-700">
                        {c.recommended_action || "NONE"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          c.state === "RECOVERED"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : c.state === "AWAITING_APPROVAL"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : c.state === "ANALYZING"
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : c.state === "HUMAN_REVIEW"
                            ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {c.state}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-emerald-400">
                      {c.recovered_amount > 0 ? formatCurrencyINR(c.recovered_amount) : "—"}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800/80 hover:bg-slate-700 transition"
                      >
                        Details <ChevronRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
