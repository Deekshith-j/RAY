"use client";

import React, { useEffect, useState } from "react";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import { BarChart3, TrendingUp, ShieldAlert, Cpu, CheckCircle2, Lock } from "lucide-react";

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/analytics/charts")
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => setData(d))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 font-mono">
      {/* Header */}
      <div className="border-b border-[#162030] pb-5">
        <div className="flex items-center gap-2 mb-1">
          <BarChart3 className="w-6 h-6 text-cyan-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Recovery Analytics &amp; Financial Telemetry
          </h1>
        </div>
        <p className="text-xs text-slate-400">
          Continuous breakdown of revenue risk exposure, intervention yields, and failure root causes.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading analytics telemetry...</div>
      ) : !data ? (
        <div className="p-12 text-center text-xs text-slate-400 space-y-1">
          <p className="text-white font-semibold">No analytics data available yet</p>
          <p>Please seed events or execute demo flows on the Overview dashboard.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Top Rates Bar */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#0A0E17] border border-[#162030]">
              <span className="text-[11px] text-slate-400 block uppercase">Recovery Rate</span>
              <p className="text-xl font-bold tabular-nums text-emerald-400 mt-1">
                {formatPercentage(data.kpis.recovery_rate_pct)}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Recovered / Total Risk</p>
            </div>

            <div className="p-4 rounded-xl bg-[#0A0E17] border border-[#162030]">
              <span className="text-[11px] text-slate-400 block uppercase">Capture Yield</span>
              <p className="text-xl font-bold tabular-nums text-blue-400 mt-1">
                {formatPercentage(data.kpis.recoverable_capture_rate_pct)}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Ground-truth recoverable captured</p>
            </div>

            <div className="p-4 rounded-xl bg-[#0A0E17] border border-[#162030]">
              <span className="text-[11px] text-slate-400 block uppercase">Verification Integrity</span>
              <p className="text-xl font-bold tabular-nums text-cyan-400 mt-1">
                {formatPercentage(data.kpis.verification_success_rate_pct)}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Dual-signal confirmation rate</p>
            </div>

            <div className="p-4 rounded-xl bg-[#0A0E17] border border-[#162030]">
              <span className="text-[11px] text-slate-400 block uppercase">Human Escalation Rate</span>
              <p className="text-xl font-bold tabular-nums text-amber-400 mt-1">
                {formatPercentage(data.kpis.human_escalation_rate_pct)}
              </p>
              <p className="text-[10px] text-slate-500 mt-1">Cases paused for &ge; ₹50k ceiling</p>
            </div>
          </div>

          {/* Breakdown Distributions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
            {/* Failure Type Distribution */}
            <div className="p-5 rounded-xl bg-[#0A0F1A] border border-[#162234] space-y-3">
              <div className="flex items-center justify-between border-b border-[#141F2E] pb-2.5">
                <h3 className="font-bold text-white uppercase text-xs">
                  Failure Type Distribution
                </h3>
                <span className="text-[10px] text-slate-400">By Exposure</span>
              </div>
              <div className="space-y-2">
                {data.failure_type_distribution.map((item: any, idx: number) => (
                  <div key={idx} className="p-2.5 bg-[#0E1522] rounded border border-[#142032] flex items-center justify-between">
                    <span className="text-slate-300">{item.name.replace(/_/g, " ")}</span>
                    <div className="text-right">
                      <span className="font-bold tabular-nums text-white">{formatCurrencyINR(item.amount)}</span>
                      <span className="text-slate-400 ml-2 text-[11px]">({item.count} cases)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Strategy Dispatch Allocation */}
            <div className="p-5 rounded-xl bg-[#0A0F1A] border border-[#162234] space-y-3">
              <div className="flex items-center justify-between border-b border-[#141F2E] pb-2.5">
                <h3 className="font-bold text-white uppercase text-xs">
                  Strategy Dispatch Allocation
                </h3>
                <span className="text-[10px] text-slate-400">By Allocation</span>
              </div>
              <div className="space-y-2">
                {data.action_distribution.map((item: any, idx: number) => (
                  <div key={idx} className="p-2.5 bg-[#0E1522] rounded border border-[#142032] flex items-center justify-between">
                    <span className="text-purple-300 font-semibold">{item.name}</span>
                    <div className="text-right">
                      <span className="font-bold tabular-nums text-emerald-400">{formatCurrencyINR(item.amount)}</span>
                      <span className="text-slate-400 ml-2 text-[11px]">({item.count} cases)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Dedicated Recoverability ML Pipeline Section */}
          <div className="p-6 rounded-xl bg-[#0B1322] border border-[#1C3252] space-y-5 shadow-lg">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#162740] pb-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-blue-400" />
                  Recoverability ML Pipeline &amp; Calibration
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Pre-action feature scoring predicting P(recovery | context) with customer-group isolation.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                  Sigmoid Calibrated
                </span>
                <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px]">
                  ray-recov-v1-production
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              <div className="p-3.5 bg-[#0E1726] rounded-lg border border-[#192A44]">
                <p className="text-slate-400 text-[10px] uppercase">Held-Out Test PR-AUC</p>
                <p className="text-xl font-bold text-emerald-400 mt-1 tabular-nums">0.8602</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Primary selection metric</p>
              </div>

              <div className="p-3.5 bg-[#0E1726] rounded-lg border border-[#192A44]">
                <p className="text-slate-400 text-[10px] uppercase">Held-Out Test ROC-AUC</p>
                <p className="text-xl font-bold text-blue-400 mt-1 tabular-nums">0.8682</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Discrimination capacity</p>
              </div>

              <div className="p-3.5 bg-[#0E1726] rounded-lg border border-[#192A44]">
                <p className="text-slate-400 text-[10px] uppercase">Calibrated Brier Score</p>
                <p className="text-xl font-bold text-purple-400 mt-1 tabular-nums">0.1372</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Probability reliability</p>
              </div>

              <div className="p-3.5 bg-[#0E1726] rounded-lg border border-[#192A44]">
                <p className="text-slate-400 text-[10px] uppercase">Revenue-Weighted Recall</p>
                <p className="text-xl font-bold text-cyan-400 mt-1 tabular-nums">95.0%</p>
                <p className="text-[10px] text-slate-400 mt-0.5">High-value capture yield</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[#0E1522] border border-[#162234] text-[11px] text-slate-300 flex items-start gap-2">
              <Lock className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-white">SAFETY INVARIANT: </strong>
                ML probabilities estimate recovery likelihood to compute Expected Recovery (Amount × P(Rec)).
                Predictions never directly authorize or trigger financial operations. The deterministic Policy Engine enforces all action boundaries.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
