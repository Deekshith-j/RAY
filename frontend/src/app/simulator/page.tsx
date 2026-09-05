"use client";

import React, { useState } from "react";
import { runSimulation, SimulationResult } from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  Sliders,
  Play,
  RotateCw,
  AlertOctagon,
  Sparkles,
  CheckCircle2,
  TrendingUp,
  Zap,
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
    <div className="space-y-8 font-mono">
      {/* Header */}
      <div className="border-b border-[#162030] pb-5">
        <div className="flex items-center gap-2 mb-1">
          <Sliders className="w-6 h-6 text-purple-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Recovery Economics Simulator
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Compare recovery strategies using deterministic synthetic cohorts.
        </p>
      </div>

      {/* Synthetic Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-[#140D07] border border-amber-500/30 text-xs text-amber-300/90 flex items-start gap-3">
        <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <strong className="text-amber-200 uppercase tracking-wider text-[11px] block">
            Synthetic Benchmark Evaluation
          </strong>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            All simulation numbers are evaluated on deterministic synthetic datasets with strict customer-group isolation.
            They demonstrate algorithmic behavior, unit economics, and safety boundaries.
          </p>
        </div>
      </div>

      {/* Key Metric Visual: Revenue Recovered per Attempted Action */}
      <div className="p-6 rounded-xl bg-[#0A0F1A] border border-[#182638] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 block">
              Core Economic Efficiency
            </span>
            <h2 className="text-base font-bold text-white tracking-tight">
              Revenue Recovered per Attempted Action
            </h2>
          </div>
          <span className="px-3 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-bold self-start sm:self-auto">
            +₹492.45 / ATTEMPT LIFT
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-4 rounded-lg bg-[#0E1522] border border-[#162234]">
            <span className="text-[10px] text-slate-400 block uppercase">Mode A: Naive Retry</span>
            <div className="text-xl font-bold tabular-nums text-slate-300 mt-1">₹2,314</div>
            <p className="text-[10px] text-slate-400 mt-1">73.5% false intervention waste</p>
          </div>

          <div className="p-4 rounded-lg bg-[#0E1522] border border-[#162234]">
            <span className="text-[10px] text-slate-400 block uppercase">Mode B: Rule-Based RAY</span>
            <div className="text-xl font-bold tabular-nums text-slate-200 mt-1">₹20,221</div>
            <p className="text-[10px] text-slate-400 mt-1">Deterministic policy enforcement</p>
          </div>

          <div className="p-4 rounded-lg bg-[#0E1B2C] border border-[#1B3556]">
            <span className="text-[10px] text-emerald-400 block uppercase font-bold">
              Mode C: ML-Assisted RAY
            </span>
            <div className="text-xl font-bold tabular-nums text-emerald-400 mt-1">₹20,713</div>
            <p className="text-[10px] text-emerald-300/80 mt-1">
              +₹492.45 / attempt &bull; 25 fewer wasted actions
            </p>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 italic">
          &ldquo;ML-assisted prioritization eliminates lower-value interventions while preserving high revenue-weighted recall.&rdquo;
        </p>
      </div>

      {/* 3 Strategy Ablation Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Strategy 1: Naive Retry */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
          <div className="border-b border-[#141F2E] pb-2.5">
            <span className="text-[10px] text-slate-400 uppercase">MODE A</span>
            <h3 className="font-bold text-white text-sm">NAIVE RETRY</h3>
            <span className="text-[10px] text-slate-400">Always retries once</span>
          </div>

          <div className="space-y-2 text-[11px] text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Actions Attempted:</span>
              <span className="text-white">1,896</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Recoveries:</span>
              <span className="text-white">503</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Revenue Recovered:</span>
              <span className="text-slate-200 font-bold">₹43,87,269</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Revenue / Action:</span>
              <span className="text-slate-200">₹2,314</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">False Interventions:</span>
              <span className="text-rose-400 font-bold">1,393 (73.5%)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Rev-Weighted Recall:</span>
              <span>15.7%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Net Economic Value:</span>
              <span className="text-slate-200">₹42,70,219</span>
            </div>
          </div>
        </div>

        {/* Strategy 2: Rule-Based RAY */}
        <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
          <div className="border-b border-[#141F2E] pb-2.5">
            <span className="text-[10px] text-blue-400 uppercase">MODE B</span>
            <h3 className="font-bold text-white text-sm">RULE-BASED RAY</h3>
            <span className="text-[10px] text-slate-400">Deterministic policy</span>
          </div>

          <div className="space-y-2 text-[11px] text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Actions Attempted:</span>
              <span className="text-white">1,330</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Recoveries:</span>
              <span className="text-emerald-400 font-bold">1,002</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Revenue Recovered:</span>
              <span className="text-emerald-400 font-bold">₹2,68,93,292</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Revenue / Action:</span>
              <span className="text-white">₹20,221</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">False Interventions:</span>
              <span className="text-amber-400">328 (24.7%)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#131E2E]">
              <span className="text-slate-400">Rev-Weighted Recall:</span>
              <span className="text-emerald-400 font-bold">96.2%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Net Economic Value:</span>
              <span className="text-emerald-400 font-bold">₹2,68,43,642</span>
            </div>
          </div>
        </div>

        {/* Strategy 3: ML-Assisted RAY */}
        <div className="p-5 rounded-xl bg-[#0B1322] border border-[#1C3252] space-y-3 shadow-lg shadow-blue-950/20">
          <div className="border-b border-[#162740] pb-2.5">
            <span className="text-[10px] text-emerald-400 uppercase font-bold">MODE C (RECOMMENDED)</span>
            <h3 className="font-bold text-white text-sm">ML-ASSISTED RAY</h3>
            <span className="text-[10px] text-emerald-300/80">Predictive EV + Policy Gate</span>
          </div>

          <div className="space-y-2 text-[11px] text-slate-300">
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">Actions Attempted:</span>
              <span className="text-white font-semibold">1,281</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">Recoveries:</span>
              <span className="text-emerald-400 font-bold">978</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">Revenue Recovered:</span>
              <span className="text-emerald-400 font-bold">₹2,65,33,316</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">Revenue / Action:</span>
              <span className="text-emerald-400 font-bold">₹20,713</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">False Interventions:</span>
              <span className="text-emerald-400 font-bold">303 (23.6%)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#132036]">
              <span className="text-slate-400">Rev-Weighted Recall:</span>
              <span className="text-emerald-400 font-bold">95.0%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Wasted Actions Cut:</span>
              <span className="text-emerald-400 font-bold">-25 actions (-7.62%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Simulation Run Console */}
      <div className="p-6 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Execute Monte Carlo Simulation Run
          </h3>
          <span className="text-[10px] text-slate-400">
            Batch Testing on Synthetic Stream
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="text-slate-400 uppercase text-[10px] block mb-2">
              Batch Size
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[100, 500, 1000, 5000].map((v) => (
                <button
                  key={v}
                  onClick={() => setCount(v)}
                  className={`py-2 rounded text-xs font-bold border transition ${
                    count === v
                      ? "bg-purple-600 text-white border-purple-500 shadow-md shadow-purple-600/30"
                      : "bg-[#0E1522] text-slate-300 border-[#182638] hover:bg-[#141E30]"
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-slate-400 uppercase text-[10px] block mb-2">
              Failure Scenario
            </label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full py-2 px-3 rounded bg-[#0E1522] border border-[#182638] text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
            >
              <option value="mixed">Mixed Scenarios (Realistic Portfolio Distribution)</option>
              <option value="network_failures">Network Timeouts & Bank Latency</option>
              <option value="checkout_abandonment">Checkout Abandonment</option>
              <option value="subscription_failures">Subscription Expiries</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleRun}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg shadow-purple-600/30 transition disabled:opacity-50"
          >
            {loading ? <RotateCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            Execute Batch Simulation
          </button>
        </div>

        {/* Dynamic Simulation Result Card */}
        {result && (
          <div className="pt-4 border-t border-[#141F2E] space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded bg-[#0E1522] border border-[#182638]">
                <span className="text-slate-400 block text-[10px] uppercase">Batch Evaluated</span>
                <span className="text-sm font-bold text-white mt-0.5 block">{result.sample_size} events</span>
              </div>
              <div className="p-3 rounded bg-[#0E1522] border border-[#182638]">
                <span className="text-slate-400 block text-[10px] uppercase">Revenue at Risk</span>
                <span className="text-sm font-bold text-rose-400 mt-0.5 block">{formatCurrencyINR(result.revenue_at_risk)}</span>
              </div>
              <div className="p-3 rounded bg-[#0E1B2C] border border-[#1B3556]">
                <span className="text-emerald-400 block text-[10px] uppercase font-bold">Economic Lift</span>
                <span className="text-sm font-bold text-emerald-400 mt-0.5 block">+{formatCurrencyINR(result.lift_revenue_recovered)} (+{result.lift_percentage}%)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
