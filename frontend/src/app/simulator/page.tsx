"use client";

import React, { useState } from "react";
import { runSimulation, SimulationResult } from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  Sliders,
  Play,
  RotateCw,
  TrendingUp,
  ShieldCheck,
  AlertOctagon,
  Sparkles,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export default function SimulatorPage() {
  const [count, setCount] = useState<number>(500);
  const [scenario, setScenario] = useState<string>("mixed");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);

  const handleRun = async () => {
    setLoading(true);
    try {
      const data = await runSimulation(count, scenario);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Sliders className="w-6 h-6 text-purple-400" />
          Revenue Failure Simulator
        </h2>
        <p className="text-sm text-slate-400">
          Deterministic Monte Carlo engine to benchmark RAY vs Baseline (naive retry) across realistic failure scenarios.
        </p>
      </div>

      {/* Benchmark Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-300/90 flex items-start gap-3">
        <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <strong className="font-semibold block text-amber-200">Evaluation &amp; Benchmark Disclaimer:</strong>
          Benchmark uses deterministic synthetic/test-mode data generated under customer-isolated splits. Results demonstrate methodology, system invariants, and economic behavior, not guaranteed live merchant performance.
        </div>
      </div>

      {/* Control Panel */}
      <div className="p-6 rounded-xl bg-[#0B1120] border border-slate-800 space-y-6 shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sample Size Options */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5">
              Failure Event Batch Size
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[100, 500, 1000, 5000].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setCount(val)}
                  className={`py-2.5 rounded-lg text-xs font-bold transition border ${
                    count === val
                      ? "bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-600/30"
                      : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800"
                  }`}
                >
                  {val.toLocaleString()}
                </button>
              ))}
            </div>
          </div>

          {/* Scenario Selection */}
          <div>
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5">
              Target Failure Scenario
            </label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full py-2.5 px-3 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 focus:outline-none focus:border-purple-500"
            >
              <option value="mixed">Mixed Scenarios (Realistic Portfolio Distribution)</option>
              <option value="network_failures">Network Timeouts & Bank Latency (High Recovery)</option>
              <option value="checkout_abandonment">Checkout Abandonment (Payment Links)</option>
              <option value="subscription_failures">Subscription Failures (Card Expiries)</option>
              <option value="payment_method_degradation">Payment Method Degradation (Bank Downtime)</option>
            </select>
          </div>
        </div>

        <div className="pt-2 flex items-center justify-end">
          <button
            onClick={handleRun}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-sm shadow-xl shadow-purple-600/30 transition disabled:opacity-50"
          >
            {loading ? <RotateCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            Execute Simulation
          </button>
        </div>
      </div>

      {/* Results Comparison */}
      {result && (
        <div className="space-y-6">
          {/* Header Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-xs text-slate-400">Total Revenue at Risk</span>
              <p className="text-2xl font-extrabold text-white mt-1">{formatCurrencyINR(result.revenue_at_risk)}</p>
              <p className="text-xs text-slate-500 mt-2">{result.sample_size} synthetic cases</p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-xs text-slate-400">Estimated Recoverable (Ground Truth)</span>
              <p className="text-2xl font-extrabold text-blue-400 mt-1">
                {formatCurrencyINR(result.estimated_recoverable_revenue)}
              </p>
              <p className="text-xs text-slate-500 mt-2">Maximum theoretical yield</p>
            </div>

            <div className="p-5 rounded-xl bg-gradient-to-br from-emerald-950/40 to-slate-900 border border-emerald-500/40">
              <span className="text-xs text-emerald-400 font-semibold">Net Economic Lift vs Baseline</span>
              <p className="text-2xl font-extrabold text-emerald-400 mt-1">
                +{formatCurrencyINR(result.lift_revenue_recovered)}
              </p>
              <p className="text-xs text-emerald-300/80 mt-2 font-medium">
                +{result.lift_percentage}% more revenue recovered
              </p>
            </div>
          </div>

          {/* Side-by-side Head-to-Head Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Baseline Card */}
            <div className="p-6 rounded-xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-bold text-slate-300 text-sm">Baseline: Naive Retry Once</h3>
                <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                  Industry Standard
                </span>
              </div>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Actions Attempted</span>
                  <span className="font-semibold text-white">{result.baseline_actions_attempted}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Successful Recoveries</span>
                  <span className="font-semibold text-white">{result.baseline_successful_recoveries}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Total Revenue Recovered</span>
                  <span className="font-bold text-lg text-slate-200">{formatCurrencyINR(result.baseline_revenue_recovered)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Recovery Rate</span>
                  <span className="font-semibold text-slate-300">{formatPercentage(result.baseline_recovery_rate_pct)}</span>
                </div>
                <div className="flex justify-between py-1 text-rose-400">
                  <span>False Interventions (Wasted Calls / Spammed Users)</span>
                  <span className="font-bold">{result.baseline_false_interventions}</span>
                </div>
              </div>
            </div>

            {/* RAY Autonomous Card */}
            <div className="p-6 rounded-xl bg-gradient-to-b from-[#0B1426] to-[#090D16] border border-purple-500/40 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-purple-500/20 pb-3">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  RAY: Risk-Aware Recovery Policy
                </h3>
                <span className="text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">
                  Autonomous Engine
                </span>
              </div>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Selective Actions Executed</span>
                  <span className="font-semibold text-white">{result.ray_actions_attempted}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Verified Recoveries</span>
                  <span className="font-bold text-emerald-400">{result.ray_successful_recoveries}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Total Revenue Recovered</span>
                  <span className="font-extrabold text-xl text-emerald-400">{formatCurrencyINR(result.ray_revenue_recovered)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">Recovery Rate</span>
                  <span className="font-bold text-emerald-400">{formatPercentage(result.ray_recovery_rate_pct)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-400">False Interventions</span>
                  <span className="font-semibold text-slate-300">{result.ray_false_interventions}</span>
                </div>
                <div className="flex justify-between py-1 text-amber-400">
                  <span>High-Value Approvals Paused (&ge; ₹50,000)</span>
                  <span className="font-bold">{result.ray_human_escalations}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sample Cases from Simulation */}
          <div className="rounded-xl bg-[#0B1120] border border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-800">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Simulated Execution Audit (Sample of 50 Events)
              </h4>
            </div>
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold sticky top-0">
                  <tr>
                    <th className="px-4 py-2.5">Case ID</th>
                    <th className="px-4 py-2.5">Amount</th>
                    <th className="px-4 py-2.5">Failure Type</th>
                    <th className="px-4 py-2.5">Score</th>
                    <th className="px-4 py-2.5">Strategy</th>
                    <th className="px-4 py-2.5">Policy Rule</th>
                    <th className="px-4 py-2.5">Status</th>
                    <th className="px-4 py-2.5">Verified Recovery</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {result.cases.map((c, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/20">
                      <td className="px-4 py-2.5 font-mono text-slate-400">{c.id.slice(0, 14)}</td>
                      <td className="px-4 py-2.5 font-semibold text-white">{formatCurrencyINR(c.amount)}</td>
                      <td className="px-4 py-2.5 font-mono text-slate-400">{c.failure_type}</td>
                      <td className="px-4 py-2.5 font-semibold text-blue-400">{(c.recoverability_score * 100).toFixed(0)}%</td>
                      <td className="px-4 py-2.5 font-mono text-[11px]">{c.final_action}</td>
                      <td className="px-4 py-2.5 text-[11px] text-slate-400">{c.policy_decision}</td>
                      <td className="px-4 py-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.status === "RECOVERED"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : c.status === "STOPPED"
                            ? "bg-slate-800 text-slate-400"
                            : "bg-rose-500/20 text-rose-400"
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-bold text-emerald-400">
                        {c.recovered_amount > 0 ? formatCurrencyINR(c.recovered_amount) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
