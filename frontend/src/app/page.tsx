"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchOverviewKPIs,
  fetchCases,
  runSimulation,
  seedDatabase,
  resetDemo,
  runFullRecovery,
  OverviewKPIs,
  RecoveryCase,
} from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCw,
  Clock,
  ChevronRight,
  Database,
  Trash2,
  Lock,
  Cpu,
  CheckCircle2,
  Activity,
  Terminal,
  FileCheck2,
  ArrowRight,
  Zap,
  Sparkles,
} from "lucide-react";

export default function OverviewPage() {
  const [kpis, setKpis] = useState<OverviewKPIs | null>(null);
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [demoExecuting, setDemoExecuting] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [kpiData, casesData] = await Promise.all([
        fetchOverviewKPIs().catch(() => null),
        fetchCases({ limit: 12 }).catch(() => []),
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
      await runSimulation(count, "mixed");
      setStatusMessage(`Simulation executed with ${count} synthetic failure events.`);
      await loadData();
      setTimeout(() => setStatusMessage(null), 5000);
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
      setStatusMessage("5,000 synthetic failure events seeded successfully.");
      await loadData();
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDemo = async () => {
    if (!window.confirm("Reset all demo cases and restore clean demonstration state?")) return;
    setResetting(true);
    try {
      const res = await resetDemo();
      setStatusMessage(`Demo reset successful: ${res.deleted_demo_cases} temporary test records purged.`);
      await loadData();
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (e: any) {
      alert("Reset failed: " + (e.message || e));
    } finally {
      setResetting(false);
    }
  };

  const handleRunDemoScenario = async (caseId: string) => {
    setDemoExecuting(caseId);
    try {
      await runFullRecovery(caseId);
      setStatusMessage(`Recovery pipeline executed for ${caseId}.`);
      await loadData();
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (e: any) {
      setStatusMessage(`Error executing ${caseId}: ${e.message}`);
    } finally {
      setDemoExecuting(null);
    }
  };

  const revenueAtRisk = kpis ? kpis.revenue_at_risk : 0;
  const revenueRecovered = kpis ? kpis.revenue_recovered : 0;
  const recoveryRate = kpis ? kpis.recovery_rate_pct : 0;
  const totalCases = kpis ? kpis.total_cases : cases.length;

  return (
    <div className="space-y-8">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#161F2E] pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Revenue Recovery Command Center
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Real-time control plane for Razorpay autonomous failure recovery, deterministic policy, and verification.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleSeed}
            disabled={loading || resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0E1624] border border-[#1C2C40] hover:bg-[#142032] text-slate-300 text-xs font-mono transition"
          >
            <Database className="w-3.5 h-3.5 text-blue-400" />
            Seed 5,000
          </button>
          <button
            onClick={() => handleRunSimulation(500)}
            disabled={simulating || resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0E1624] border border-[#1C2C40] hover:bg-[#142032] text-slate-300 text-xs font-mono transition disabled:opacity-50"
          >
            {simulating ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current text-purple-400" />}
            Simulate 500
          </button>
          <button
            onClick={handleResetDemo}
            disabled={resetting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-rose-950/20 border border-rose-800/40 hover:bg-rose-900/40 text-rose-300 text-xs font-mono transition disabled:opacity-50"
            title="Reset demonstration test data"
          >
            {resetting ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
            Reset Demo
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-lg bg-[#0E1B2C] border border-[#1B3556] text-xs font-mono text-emerald-400 flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* Top 4 Financial Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Revenue at Risk */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Revenue at Risk
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              EXPOSURE
            </span>
          </div>
          <div className="text-2xl font-bold font-mono tabular-nums text-white tracking-tight">
            {formatCurrencyINR(revenueAtRisk)}
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-2">
            Total failed volume across {totalCases.toLocaleString()} cases
          </p>
        </div>

        {/* Metric 2: Recovered */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Recovered
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              PROVEN
            </span>
          </div>
          <div className="text-2xl font-bold font-mono tabular-nums text-emerald-400 tracking-tight">
            {formatCurrencyINR(revenueRecovered)}
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-2">
            Autonomous + approved human recoveries
          </p>
        </div>

        {/* Metric 3: Recovery Rate */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Recovery Rate
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
              YIELD
            </span>
          </div>
          <div className="text-2xl font-bold font-mono tabular-nums text-blue-400 tracking-tight">
            {formatPercentage(recoveryRate)}
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-2">
            Recovered / Total revenue at risk
          </p>
        </div>

        {/* Metric 4: Verified Revenue */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              Verified Revenue
            </span>
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              DUAL-SIGNAL
            </span>
          </div>
          <div className="text-2xl font-bold font-mono tabular-nums text-emerald-400 tracking-tight">
            {formatCurrencyINR(revenueRecovered)}
          </div>
          <p className="text-[11px] text-slate-400 font-mono mt-2">
            API Poll + HMAC Webhook signature verified
          </p>
        </div>
      </div>

      {/* Hero System Status Box */}
      <div className="p-5 rounded-xl bg-[#0A0F1A] border border-[#192638] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-mono font-bold tracking-wider uppercase text-white">
              RAY AUTONOMY STATUS
            </span>
          </div>
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            ACTIVE
          </span>
        </div>

        <div className="text-xs font-mono text-slate-300 leading-relaxed space-y-1">
          <p>AI may recommend actions. Deterministic policy controls authorization.</p>
          <p>Financial execution requires policy authorization.</p>
        </div>

        <div className="pt-2 border-t border-[#141F2E] flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-400">
          <span className="text-blue-400 font-semibold">Prediction</span>
          <span>&rarr;</span>
          <span className="text-purple-400 font-semibold">Recommendation</span>
          <span>&rarr;</span>
          <span className="text-amber-400 font-semibold">Authorization</span>
          <span>&rarr;</span>
          <span className="text-cyan-400 font-semibold">Execution</span>
          <span>&rarr;</span>
          <span className="text-emerald-400 font-semibold">Verification</span>
        </div>
      </div>

      {/* Recovery Pipeline Visualization */}
      <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
            Closed-Loop Financial Recovery Pipeline
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            PREDICTION &ne; AUTHORIZATION &ne; EXECUTION
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 font-mono text-[11px]">
          {[
            { step: "01", label: "FAILED", color: "text-rose-400", border: "border-rose-500/20", bg: "bg-rose-500/5" },
            { step: "02", label: "DETECTED", color: "text-blue-400", border: "border-blue-500/20", bg: "bg-blue-500/5" },
            { step: "03", label: "DIAGNOSED", color: "text-blue-400", border: "border-blue-500/20", bg: "bg-blue-500/5" },
            { step: "04", label: "PLANNED", color: "text-purple-400", border: "border-purple-500/20", bg: "bg-purple-500/5" },
            { step: "05", label: "AUTHORIZED", color: "text-amber-400", border: "border-amber-500/20", bg: "bg-amber-500/5" },
            { step: "06", label: "EXECUTED", color: "text-cyan-400", border: "border-cyan-500/20", bg: "bg-cyan-500/5" },
            { step: "07", label: "VERIFIED", color: "text-emerald-400", border: "border-emerald-500/20", bg: "bg-emerald-500/5" },
            { step: "08", label: "RECOVERED", color: "text-emerald-400 font-bold", border: "border-emerald-500/40", bg: "bg-emerald-500/10" },
          ].map((s) => (
            <div
              key={s.step}
              className={`p-2.5 rounded-lg border ${s.border} ${s.bg} text-center space-y-0.5`}
            >
              <span className="text-[9px] text-slate-400 block font-semibold">{s.step}</span>
              <span className={`text-[11px] ${s.color} block`}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Demo Scenarios Quick Launcher */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-white">
              Demonstration Scenarios (Buildathon Judge Flows)
            </h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            5 Deterministic Test Harnesses
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Scenario 1 */}
          <div className="p-3.5 rounded-lg bg-[#0A0F1A] border border-[#162234] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-400">SCENARIO 1</span>
                <span className="text-[10px] font-mono font-bold text-emerald-400">AUTONOMOUS</span>
              </div>
              <h3 className="font-semibold text-xs text-white">PAY_DEMO_001</h3>
              <p className="text-[11px] font-mono text-emerald-400 mt-0.5">₹24,999.00</p>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                Transient timeout &rarr; auto-retry allowed &rarr; dual verified.
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-2 border-t border-[#141F2E]">
              <Link
                href="/cases/PAY_DEMO_001"
                className="flex-1 py-1 text-center rounded bg-[#111A29] hover:bg-[#162337] text-[10px] font-mono text-slate-300 transition"
              >
                Inspect
              </Link>
              <button
                onClick={() => handleRunDemoScenario("PAY_DEMO_001")}
                disabled={demoExecuting === "PAY_DEMO_001"}
                className="px-2 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-[10px] font-mono text-emerald-400 border border-emerald-500/30 transition disabled:opacity-50"
              >
                {demoExecuting === "PAY_DEMO_001" ? "Running..." : "Run"}
              </button>
            </div>
          </div>

          {/* Scenario 2 */}
          <div className="p-3.5 rounded-lg bg-[#0A0F1A] border border-[#162234] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-400">SCENARIO 2</span>
                <span className="text-[10px] font-mono font-bold text-amber-400">HUMAN GATE</span>
              </div>
              <h3 className="font-semibold text-xs text-white">PAY_DEMO_HIGH_VALUE</h3>
              <p className="text-[11px] font-mono text-amber-400 mt-0.5">₹75,000.00</p>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                High-value &ge; ₹50,000 &rarr; policy freeze &rarr; operator approval.
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-2 border-t border-[#141F2E]">
              <Link
                href="/cases/PAY_DEMO_HIGH_VALUE"
                className="flex-1 py-1 text-center rounded bg-[#111A29] hover:bg-[#162337] text-[10px] font-mono text-slate-300 transition"
              >
                Inspect
              </Link>
              <button
                onClick={() => handleRunDemoScenario("PAY_DEMO_HIGH_VALUE")}
                disabled={demoExecuting === "PAY_DEMO_HIGH_VALUE"}
                className="px-2 py-1 rounded bg-amber-600/20 hover:bg-amber-600/30 text-[10px] font-mono text-amber-400 border border-amber-500/30 transition disabled:opacity-50"
              >
                {demoExecuting === "PAY_DEMO_HIGH_VALUE" ? "Running..." : "Run"}
              </button>
            </div>
          </div>

          {/* Scenario 3 */}
          <div className="p-3.5 rounded-lg bg-[#0A0F1A] border border-[#162234] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-400">SCENARIO 3</span>
                <span className="text-[10px] font-mono font-bold text-rose-400">CONFLICT</span>
              </div>
              <h3 className="font-semibold text-xs text-white">PAY_DEMO_CONFLICT</h3>
              <p className="text-[11px] font-mono text-rose-400 mt-0.5">₹15,000.00</p>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                API captured vs Webhook failed &rarr; discrepancy &rarr; HUMAN_REVIEW.
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-2 border-t border-[#141F2E]">
              <Link
                href="/cases/PAY_DEMO_CONFLICT"
                className="flex-1 py-1 text-center rounded bg-[#111A29] hover:bg-[#162337] text-[10px] font-mono text-slate-300 transition"
              >
                Inspect
              </Link>
              <button
                onClick={() => handleRunDemoScenario("PAY_DEMO_CONFLICT")}
                disabled={demoExecuting === "PAY_DEMO_CONFLICT"}
                className="px-2 py-1 rounded bg-rose-600/20 hover:bg-rose-600/30 text-[10px] font-mono text-rose-400 border border-rose-500/30 transition disabled:opacity-50"
              >
                {demoExecuting === "PAY_DEMO_CONFLICT" ? "Running..." : "Run"}
              </button>
            </div>
          </div>

          {/* Scenario 4 */}
          <div className="p-3.5 rounded-lg bg-[#0A0F1A] border border-[#162234] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-400">SCENARIO 4</span>
                <span className="text-[10px] font-mono font-bold text-cyan-400">INJECTION</span>
              </div>
              <h3 className="font-semibold text-xs text-white truncate">PAY_DEMO_INJECTION</h3>
              <p className="text-[11px] font-mono text-cyan-400 mt-0.5">₹1,00,000.00</p>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                Adversarial prompt in customer notes &rarr; &lt;UNTRUSTED_DATA&gt; bounded.
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-2 border-t border-[#141F2E]">
              <Link
                href="/cases/PAY_DEMO_INJECTION"
                className="flex-1 py-1 text-center rounded bg-[#111A29] hover:bg-[#162337] text-[10px] font-mono text-slate-300 transition"
              >
                Inspect
              </Link>
              <button
                onClick={() => handleRunDemoScenario("PAY_DEMO_INJECTION")}
                disabled={demoExecuting === "PAY_DEMO_INJECTION"}
                className="px-2 py-1 rounded bg-cyan-600/20 hover:bg-cyan-600/30 text-[10px] font-mono text-cyan-400 border border-cyan-500/30 transition disabled:opacity-50"
              >
                {demoExecuting === "PAY_DEMO_INJECTION" ? "Running..." : "Run"}
              </button>
            </div>
          </div>

          {/* Scenario 5 */}
          <div className="p-3.5 rounded-lg bg-[#0A0F1A] border border-[#162234] flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono text-slate-400">SCENARIO 5</span>
                <span className="text-[10px] font-mono font-bold text-blue-400">IDEMPOTENCY</span>
              </div>
              <h3 className="font-semibold text-xs text-white">PAY_DEMO_DUPLICATE</h3>
              <p className="text-[11px] font-mono text-blue-400 mt-0.5">₹5,000.00</p>
              <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                Duplicate request &rarr; canonical key match &rarr; cached response.
              </p>
            </div>
            <div className="flex items-center gap-1.5 pt-2 border-t border-[#141F2E]">
              <Link
                href="/cases/PAY_DEMO_DUPLICATE"
                className="flex-1 py-1 text-center rounded bg-[#111A29] hover:bg-[#162337] text-[10px] font-mono text-slate-300 transition"
              >
                Inspect
              </Link>
              <button
                onClick={() => handleRunDemoScenario("PAY_DEMO_DUPLICATE")}
                disabled={demoExecuting === "PAY_DEMO_DUPLICATE"}
                className="px-2 py-1 rounded bg-blue-600/20 hover:bg-blue-600/30 text-[10px] font-mono text-blue-400 border border-blue-500/30 transition disabled:opacity-50"
              >
                {demoExecuting === "PAY_DEMO_DUPLICATE" ? "Running..." : "Run"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Live Recovery Activity Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold font-mono uppercase tracking-wider text-white">
              Live Recovery Activity
            </h2>
          </div>
          <Link
            href="/cases"
            className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            View All Cases ({totalCases.toLocaleString()}) &rarr;
          </Link>
        </div>

        <div className="rounded-xl border border-[#162234] bg-[#0A0F1A] overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-400">Loading cases...</div>
          ) : cases.length === 0 ? (
            <div className="p-8 text-center space-y-1">
              <p className="text-xs font-semibold text-slate-300">No recovery cases yet</p>
              <p className="text-[11px] text-slate-400 font-mono">
                RAY will surface revenue-at-risk opportunities as payment failure events arrive.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0D1524] text-slate-400 border-b border-[#162234] uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="py-2.5 px-4">Case ID</th>
                    <th className="py-2.5 px-4">Amount at Risk</th>
                    <th className="py-2.5 px-4">Diagnosis</th>
                    <th className="py-2.5 px-4">Recommendation</th>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#131E2E] text-slate-300">
                  {cases.map((c) => (
                    <tr key={c.id} className="hover:bg-[#0E1626] transition-colors">
                      <td className="py-3 px-4 font-bold text-white whitespace-nowrap">
                        <Link href={`/cases/${c.id}`} className="text-blue-400 hover:underline">
                          {c.id}
                        </Link>
                      </td>
                      <td className="py-3 px-4 font-bold tabular-nums whitespace-nowrap">
                        {formatCurrencyINR(c.amount_at_risk)}
                      </td>
                      <td className="py-3 px-4 text-slate-300 whitespace-nowrap truncate max-w-[160px]">
                        {c.failure_type.replace(/_/g, " ")}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded bg-[#111A29] border border-[#1D2C42] text-[10px] text-slate-200">
                          {c.recommended_action || "RETRY"}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            c.state === "RECOVERED"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : c.state === "AWAITING_APPROVAL"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                              : c.state === "HUMAN_REVIEW"
                              ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                              : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                          }`}
                        >
                          {c.state}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <Link
                          href={`/cases/${c.id}`}
                          className="px-2.5 py-1 rounded bg-[#121B2B] hover:bg-[#182438] text-[10px] text-slate-300 border border-[#1F2E45] transition inline-block"
                        >
                          Inspect &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
