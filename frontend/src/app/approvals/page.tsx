"use client";

import React, { useEffect, useState } from "react";
import { fetchCases, RecoveryCase } from "@/lib/api";
import { formatCurrencyINR, formatPercentage } from "@/lib/formatters";
import {
  ShieldAlert,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RotateCw,
  UserCheck,
  FileText,
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
      const res = await fetch(`http://localhost:8000/api/v1/cases/${caseId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          approved,
          reviewer_name: "Operations Lead (You)",
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-amber-400" />
            Human Authorization Queue
          </h2>
          <p className="text-sm text-slate-400">
            Mandatory human review for actions exceeding ₹50,000 policy threshold or flagged risk exceptions.
          </p>
        </div>
        <button
          onClick={loadApprovalCases}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-700 transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
          Refresh Queue
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 flex items-center justify-center gap-3">
          <RotateCw className="w-5 h-5 animate-spin text-blue-500" />
          <span>Loading approval queue...</span>
        </div>
      ) : cases.length === 0 ? (
        <div className="p-12 rounded-xl bg-slate-900/50 border border-slate-800 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
            <UserCheck className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-white">All Clear! No Pending Approvals</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            All high-value actions (&ge; ₹50,000) have been reviewed. Cases under ₹50,000 continue through automated bounded execution.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {cases.map((c) => (
            <div
              key={c.id}
              className="p-6 rounded-xl bg-[#0B1120] border border-amber-500/30 shadow-xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-slate-400 font-semibold">{c.id}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40">
                      REQUIRES APPROVAL (&ge; ₹50,000)
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Customer: <strong className="text-slate-200">{c.customer_name || c.customer_id}</strong> ({c.customer_email || "N/A"})
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">Revenue at Risk</p>
                  <p className="text-2xl font-extrabold text-white">{formatCurrencyINR(c.amount_at_risk)}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <p className="text-slate-400">Proposed Strategy</p>
                  <p className="text-sm font-bold text-blue-400 mt-0.5 font-mono">{c.recommended_action || "PAYMENT_LINK"}</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    ML Confidence: <strong>{c.ai_confidence ? formatPercentage(c.ai_confidence * 100) : "91%"}</strong>
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <p className="text-slate-400">Expected Recovery Value</p>
                  <p className="text-sm font-bold text-emerald-400 mt-0.5">
                    {formatCurrencyINR(c.expected_recovery_value)}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    P(Recoverable): {(c.recoverability_score * 100).toFixed(0)}%
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800">
                  <p className="text-slate-400">Policy Reason</p>
                  <p className="text-xs font-medium text-amber-300 mt-0.5">
                    Amount &ge; ₹50,000. Human authorization required before tool invocation.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/80 text-xs">
                <p className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-400" />
                  AI Diagnosis & Evidence:
                </p>
                <p className="text-slate-300 leading-relaxed">
                  {c.ai_diagnosis || c.failure_reason}
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  onClick={() => handleDecision(c.id, false)}
                  disabled={processingId === c.id}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border border-rose-800 text-xs font-bold transition disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  REJECT
                </button>
                <button
                  onClick={() => handleDecision(c.id, true)}
                  disabled={processingId === c.id}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  APPROVE RECOVERY ACTION
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
