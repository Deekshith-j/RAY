"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchCases, RecoveryCase } from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  UserCheck,
  FileText,
  Lock,
} from "lucide-react";

export default function ApprovalsPage() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const loadApprovalCases = async () => {
    setLoading(true);
    try {
      const data = await fetchCases({ state: "AWAITING_APPROVAL", limit: 50 });
      setCases(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovalCases();
  }, []);

  const handleDecision = async (caseId: string, approved: boolean) => {
    setProcessingId(caseId);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/cases/${caseId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          approved,
          reviewer_name: "Risk Lead (You)",
          notes: approved
            ? "Approved high-value recovery execution after policy verification."
            : "Rejected high-value recovery execution due to risk policy.",
        }),
      });
      if (res.ok) {
        await loadApprovalCases();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#162030] pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="w-6 h-6 text-amber-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">Human Authorization Queue</h1>
          </div>
          <p className="text-xs text-slate-400">
            Mandatory operator review for transactions &ge; ₹50,000 policy threshold or flagged risk exceptions.
          </p>
        </div>
        <button
          onClick={loadApprovalCases}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0E1624] border border-[#1C2C40] text-xs text-slate-300 hover:bg-[#142032] transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
          Refresh Queue
        </button>
      </div>

      {/* Top Operational Counter Banner */}
      <div
        className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
          cases.length > 0
            ? "bg-[#140D07] border-amber-500/40 text-amber-300"
            : "bg-[#09121E] border-[#16253A] text-slate-400"
        }`}
      >
        <div className="flex items-center gap-2.5">
          <span
            className={`w-2 h-2 rounded-full ${
              cases.length > 0 ? "bg-amber-400 animate-pulse" : "bg-emerald-400"
            }`}
          />
          <span className="font-bold uppercase tracking-wider text-xs">
            {cases.length} {cases.length === 1 ? "ACTION REQUIRES" : "ACTIONS REQUIRE"} HUMAN AUTHORIZATION
          </span>
        </div>
        <span className="text-[11px] text-slate-400 hidden sm:inline">
          Policy Rule 7 Enforced (&ge; ₹50,000)
        </span>
      </div>

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex items-center justify-center gap-3">
          <RotateCw className="w-4 h-4 animate-spin text-amber-400" />
          <span>Loading approval queue...</span>
        </div>
      ) : cases.length === 0 ? (
        <div className="p-12 rounded-xl bg-[#0A0E17] border border-[#162030] text-center space-y-3">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto">
            <UserCheck className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-white">All Clear — No Pending Approvals</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            All high-value transactions (&ge; ₹50,000) have been reviewed. Cases under ₹50,000 continue through automated bounded execution.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {cases.map((c) => (
            <div
              key={c.id}
              className="p-6 rounded-xl bg-[#0A0F1A] border border-amber-500/30 shadow-xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#141E2C] pb-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <Link href={`/cases/${c.id}`} className="text-sm font-bold text-white hover:underline">
                      {c.id}
                    </Link>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 font-bold border border-amber-500/30">
                      HIGH RISK (&ge; ₹50,000)
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Customer: <span className="text-slate-200">{c.customer_name || c.customer_id}</span> ({c.customer_email || "N/A"})
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block uppercase">Revenue at Risk</span>
                  <span className="text-xl font-bold tabular-nums text-white">{formatCurrencyINR(c.amount_at_risk)}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-[#0E1522] border border-[#182638]">
                  <span className="text-slate-400 block text-[10px] uppercase">AI Recommendation</span>
                  <p className="text-sm font-bold text-blue-400 mt-0.5">{c.recommended_action || "RETRY"}</p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    ML Probability: <strong>{c.ai_confidence ? formatPercentage(c.ai_confidence * 100) : "91%"}</strong>
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-[#0E1522] border border-[#182638]">
                  <span className="text-slate-400 block text-[10px] uppercase">Policy Gate Decision</span>
                  <p className="text-xs font-bold text-amber-300 mt-1">
                    BLOCKED — HUMAN APPROVAL
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Tool execution halted at gateway
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-[#0E1522] border border-[#182638]">
                  <span className="text-slate-400 block text-[10px] uppercase">Expected Recovery</span>
                  <p className="text-sm font-bold text-emerald-400 mt-0.5 tabular-nums">
                    {formatCurrencyINR(c.expected_recovery_value)}
                  </p>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Expected net value after action cost
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#0B111C] border border-[#141F2E] text-xs">
                <span className="text-slate-400 block text-[10px] uppercase mb-1">Diagnosis &amp; Reason</span>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {c.ai_diagnosis || c.failure_reason}
                </p>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[11px] text-slate-400 italic">
                  AI recommended it &ne; system authorized it
                </span>
                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => handleDecision(c.id, false)}
                    disabled={processingId === c.id}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-[#181111] hover:bg-[#241717] text-rose-300 border border-rose-800/60 text-xs font-bold transition disabled:opacity-50"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecision(c.id, true)}
                    disabled={processingId === c.id}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold shadow-lg shadow-amber-500/20 transition disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 fill-current" />
                    Approve Recovery Action
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
