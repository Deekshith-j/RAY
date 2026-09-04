"use client";

import React, { useEffect, useState } from "react";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import { BarChart3, TrendingUp, ShieldAlert, Cpu, CheckCircle } from "lucide-react";

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
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-cyan-400" />
          Recovery Analytics & Financial Telemetry
        </h2>
        <p className="text-sm text-slate-400">
          Continuous breakdown of revenue risk exposure, intervention yields, and failure root causes.
        </p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500">Loading analytics data...</div>
      ) : !data ? (
        <div className="p-12 text-center text-slate-500">
          No analytics data available yet. Please seed demo events or run the failure simulator.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Key Rates Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">Recovery Rate</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                {formatPercentage(data.kpis.recovery_rate_pct)}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">Capture Yield</span>
              <p className="text-xl font-bold text-blue-400 mt-1">
                {formatPercentage(data.kpis.recoverable_capture_rate_pct)}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">Verification Integrity</span>
              <p className="text-xl font-bold text-cyan-400 mt-1">
                {formatPercentage(data.kpis.verification_success_rate_pct)}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-xs text-slate-400">Human Escalation Rate</span>
              <p className="text-xl font-bold text-amber-400 mt-1">
                {formatPercentage(data.kpis.human_escalation_rate_pct)}
              </p>
            </div>
          </div>

          {/* Breakdown Tables */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Failure Type Distribution */}
            <div className="p-6 rounded-xl bg-[#0B1120] border border-slate-800 space-y-4">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                Failure Type Distribution
              </h3>
              <div className="space-y-2">
                {data.failure_type_distribution.map((item: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-900/60 rounded-lg flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-300">{item.name}</span>
                    <div className="text-right">
                      <span className="font-bold text-white">{formatCurrencyINR(item.amount)}</span>
                      <span className="text-slate-500 ml-2">({item.count} cases)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Action Distribution */}
            <div className="p-6 rounded-xl bg-[#0B1120] border border-slate-800 space-y-4">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                Strategy Dispatch Allocation
              </h3>
              <div className="space-y-2">
                {data.action_distribution.map((item: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-900/60 rounded-lg flex items-center justify-between text-xs">
                    <span className="font-mono text-purple-300 font-semibold">{item.name}</span>
                    <div className="text-right">
                      <span className="font-bold text-emerald-400">{formatCurrencyINR(item.amount)}</span>
                      <span className="text-slate-500 ml-2">({item.count} cases)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Dedicated Recoverability ML Pipeline Section */}
          <div className="p-6 rounded-xl bg-gradient-to-br from-[#0B1426] to-[#090D16] border border-blue-500/30 space-y-6 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-blue-400" />
                  Recoverability ML Pipeline & Calibration
                </h3>
                <p className="text-xs text-slate-400">
                  Pre-action feature scoring predicting P(successful_recovery | context).
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold">
                  Sigmoid Calibrated
                </span>
                <span className="px-2.5 py-1 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono">
                  ray-recov-v1-production
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800">
                <p className="text-slate-400">Held-Out Test PR-AUC</p>
                <p className="text-xl font-bold text-emerald-400 mt-1">0.8602</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Primary selection metric</p>
              </div>
              <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800">
                <p className="text-slate-400">Held-Out Test ROC-AUC</p>
                <p className="text-xl font-bold text-blue-400 mt-1">0.8682</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Discrimination capacity</p>
              </div>
              <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800">
                <p className="text-slate-400">Calibrated Brier Score</p>
                <p className="text-xl font-bold text-purple-400 mt-1">0.1372</p>
                <p className="text-[11px] text-slate-500 mt-0.5">Probability reliability</p>
              </div>
              <div className="p-3.5 bg-slate-900/70 rounded-lg border border-slate-800">
                <p className="text-slate-400">Precision / Recall (F1)</p>
                <p className="text-xl font-bold text-cyan-400 mt-1">0.8350</p>
                <p className="text-[11px] text-slate-500 mt-0.5">At standard threshold</p>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-900/40 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
              <span className="text-blue-400 font-bold">SAFETY NOTICE:</span>
              <span>
                ML probabilities estimate recovery likelihood to compute Expected Recovery (Amount at Risk × P(Rec)).
                Predictions never directly authorize or trigger financial operations. The deterministic Policy Engine enforces all action boundaries.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
