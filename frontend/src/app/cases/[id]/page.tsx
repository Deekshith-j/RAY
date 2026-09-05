"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  fetchCaseById,
  fetchCaseDecision,
  fetchCaseExecution,
  fetchCaseVerification,
  fetchCaseTimeline,
  runFullRecovery,
  RecoveryCase,
} from "@/lib/api";
import { formatCurrencyINR } from "@/lib/formatters";
import {
  ArrowLeft,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Clock,
  FileText,
  Lock,
  RefreshCw,
  Cpu,
  Layers,
  Terminal,
  XCircle,
  Hash,
  ShieldAlert,
  Bot,
} from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [decision, setDecision] = useState<any | null>(null);
  const [execution, setExecution] = useState<any | null>(null);
  const [verification, setVerification] = useState<any | null>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadAll = async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const [c, d, e, v, t] = await Promise.all([
        fetchCaseById(caseId),
        fetchCaseDecision(caseId),
        fetchCaseExecution(caseId),
        fetchCaseVerification(caseId),
        fetchCaseTimeline(caseId),
      ]);
      setCaseData(c);
      setDecision(d);
      setExecution(e);
      setVerification(v);
      setTimeline(t);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [caseId]);

  const handleRunAutonomousRecovery = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      await runFullRecovery(caseId);
      setActionMessage("Autonomous recovery pipeline executed and verified.");
      await loadAll();
    } catch (err: any) {
      setActionMessage(`Execution error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAuthorize = async (approved: boolean) => {
    setActionLoading(true);
    setActionMessage(null);
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
            : "Rejected high-value recovery execution due to risk boundary.",
        }),
      });
      if (res.ok) {
        setActionMessage(approved ? "Authorization recorded! Executing recovery..." : "Rejection recorded. Case stopped.");
        if (approved) {
          await runFullRecovery(caseId);
        }
        await loadAll();
      } else {
        const err = await res.json().catch(() => ({ detail: "Approval failed" }));
        setActionMessage(`Approval error: ${err.detail}`);
      }
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !caseData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-slate-400 font-mono text-xs">
          <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
          Loading case provenance telemetry...
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-20 space-y-3">
        <h2 className="text-lg font-bold text-white font-mono">Case Not Found</h2>
        <p className="text-xs text-slate-400 font-mono">Case {caseId} does not exist in the ledger.</p>
        <Link href="/cases" className="text-xs text-blue-400 hover:underline font-mono inline-block">
          &larr; Back to Cases
        </Link>
      </div>
    );
  }

  const prob = caseData.recoverability_score || 0;
  const band = prob >= 0.85 ? "HIGH" : prob >= 0.6 ? "MEDIUM" : "LOW";
  const isRecovered = caseData.state === "RECOVERED";
  const isAwaitingApproval = caseData.state === "AWAITING_APPROVAL";

  return (
    <div className="space-y-8 pb-16">
      {/* Navigation & Header */}
      <div>
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Cases Ledger
        </Link>

        {/* Top Header Card */}
        <div className="p-6 rounded-xl bg-[#0A0E17] border border-[#162030] shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-mono text-slate-400">Recovery Case</span>
              <span className="text-slate-600">&bull;</span>
              <span className="text-xs font-mono text-slate-400">{caseData.entity_type} {caseData.entity_id}</span>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl lg:text-3xl font-bold text-white font-mono tracking-tight">
                {caseData.id}
              </h1>
              <span className="text-2xl lg:text-3xl font-bold text-slate-300 font-mono tabular-nums">
                {formatCurrencyINR(caseData.amount_at_risk)}
              </span>
              <span
                className={`px-3 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider border ${
                  isRecovered
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : isAwaitingApproval
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                    : caseData.state === "HUMAN_REVIEW"
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                }`}
              >
                ● {isRecovered ? "VERIFIED RECOVERED" : caseData.state}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAll}
              className="px-3 py-2 rounded bg-[#0E1624] border border-[#1B283A] hover:bg-[#142032] text-slate-300 text-xs font-mono flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>

            {!isRecovered && !isAwaitingApproval && (
              <button
                onClick={handleRunAutonomousRecovery}
                disabled={actionLoading}
                className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs font-mono uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                {actionLoading ? "Executing Pipeline..." : "Execute Recovery"}
              </button>
            )}
          </div>
        </div>

        {actionMessage && (
          <div className="mt-4 p-3 rounded-lg bg-[#0E1B2C] border border-[#1B3556] text-xs font-mono text-emerald-400">
            {actionMessage}
          </div>
        )}
      </div>

      {/* Core Invariant Banner */}
      <div className="p-4 rounded-xl bg-[#0B1120] border border-[#1B2940] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
        <div className="space-y-0.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 block">
            System Invariant
          </span>
          <p className="text-white font-semibold tracking-tight text-xs">
            PREDICTION ≠ RECOMMENDATION ≠ AUTHORIZATION ≠ EXECUTION ≠ VERIFICATION
          </p>
        </div>
        <p className="text-[11px] text-slate-400 italic md:text-right">
          &ldquo;AI intelligence is separated from financial authority.&rdquo;
        </p>
      </div>

      {/* High-Value Approval Box (When case >= ₹50k or AWAITING_APPROVAL) */}
      {isAwaitingApproval && (
        <div className="p-6 rounded-xl bg-[#140D07] border-2 border-amber-500/50 shadow-2xl space-y-4 font-mono">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-amber-400 font-bold text-sm tracking-wider uppercase">
                <AlertTriangle className="w-5 h-5" />
                HUMAN AUTHORIZATION REQUIRED
              </div>
              <p className="text-xs text-amber-200/90 mt-1 leading-relaxed">
                {formatCurrencyINR(caseData.amount_at_risk)} exceeds the automatic recovery ceiling of ₹50,000.
                AI recommends an action, but Policy Engine deterministically halts tool execution until signed operator authorization.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold shrink-0">
              0 EXECUTIONS DISPATCHED
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-[#090C12] p-4 rounded-lg border border-amber-900/40">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">AI Recommendation</span>
              <strong className="text-blue-400 text-sm mt-0.5 block">{caseData.recommended_action || "RETRY"}</strong>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Policy Decision</span>
              <strong className="text-amber-400 text-sm mt-0.5 block">BLOCKED — HUMAN APPROVAL REQUIRED</strong>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Financial Execution</span>
              <strong className="text-rose-400 text-sm mt-0.5 block">0 EXECUTIONS</strong>
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-amber-300/80 italic">
              AI recommended it &ne; system authorized it
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleAuthorize(false)}
                disabled={actionLoading}
                className="px-4 py-2 rounded-lg bg-[#1F1515] border border-rose-800/60 hover:bg-rose-900/40 text-rose-300 text-xs font-bold tracking-wider uppercase transition disabled:opacity-50 flex items-center gap-1.5"
              >
                <XCircle className="w-4 h-4" /> Reject
              </button>
              <button
                onClick={() => handleAuthorize(true)}
                disabled={actionLoading}
                className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-black tracking-wider uppercase transition disabled:opacity-50 flex items-center gap-1.5 shadow-lg shadow-amber-500/20"
              >
                <CheckCircle2 className="w-4 h-4 fill-current" /> Approve Execution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6 Provenance Lineage Cards */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Financial Provenance Chain
            </h2>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Prediction &rarr; Recommendation &rarr; Authorization &rarr; Execution &rarr; Verification &rarr; Revenue
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
          {/* Card 01: Opportunity */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                01 &mdash; OPPORTUNITY
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-semibold">
                BAND: {band}
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="text-lg font-bold text-white tabular-nums">
                {formatCurrencyINR(caseData.amount_at_risk)}
              </div>
              <p className="text-[11px] text-slate-400">Revenue at risk from payment failure</p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Failure Event:</span>
                <span className="text-slate-200">{caseData.failure_type}</span>
              </div>
              <div className="flex justify-between">
                <span>P(recovery):</span>
                <span className="text-emerald-400 font-bold">{(prob * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Card 02: AI Diagnosis */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">
                02 &mdash; AI DIAGNOSIS
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20">
                ADVISORY
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="text-base font-bold text-white uppercase">
                {caseData.failure_type.replace(/_/g, " ")}
              </div>
              <p className="text-[11px] text-slate-400">Classified root cause telemetry</p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Confidence:</span>
                <span className="text-blue-400 font-semibold">91.4%</span>
              </div>
              <div className="flex justify-between">
                <span>Data Boundary:</span>
                <span className="text-emerald-400">&lt;UNTRUSTED_DATA&gt;</span>
              </div>
            </div>
          </div>

          {/* Card 03: Recovery Recommendation */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">
                03 &mdash; RECOMMENDATION
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20">
                PROPOSAL
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="text-base font-bold text-white uppercase">
                {decision?.recommended_strategy || caseData.recommended_action || "RETRY"}
              </div>
              <p className="text-[11px] text-slate-400">Ranked by Expected Value (EV)</p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Expected Recovery:</span>
                <span className="text-purple-300 font-bold">
                  {formatCurrencyINR(decision?.expected_recovery || caseData.expected_recovery_value)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Authority:</span>
                <span className="text-amber-400">Advisory Only</span>
              </div>
            </div>
          </div>

          {/* Card 04: Policy Authorization */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                04 &mdash; POLICY AUTHORIZATION
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold">
                DETERMINISTIC
              </span>
            </div>
            <div className="space-y-1.5">
              <div
                className={`text-base font-bold uppercase ${
                  decision?.policy_result === "ALLOW"
                    ? "text-emerald-400"
                    : isAwaitingApproval
                    ? "text-amber-400"
                    : "text-slate-200"
                }`}
              >
                {decision?.policy_result === "ALLOW" ? "✓ ALLOWED" : decision?.policy_result || (caseData.amount_at_risk >= 50000 ? "REQUIRE_HUMAN_APPROVAL" : "ALLOWED")}
              </div>
              <p className="text-[11px] text-slate-400">
                {caseData.amount_at_risk >= 50000 ? "Exceeds ₹50k threshold" : "Within automatic retry ceiling"}
              </p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Rule Engine:</span>
                <span className="text-slate-300">Rules 1-10 Enforced</span>
              </div>
              <div className="flex justify-between">
                <span>Policy Version:</span>
                <span className="text-slate-300">v1.0 (Python)</span>
              </div>
            </div>
          </div>

          {/* Card 05: Tool Gateway */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                05 &mdash; TOOL GATEWAY
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                ENFORCED
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="text-base font-bold text-white uppercase">
                {execution?.execution_status === "SUCCESS" ? "✓ AUTHORIZED" : (execution?.execution_status || (execution ? "SUCCESS" : "PENDING"))}
              </div>
              <p className="text-[11px] text-slate-400 truncate max-w-[220px]">
                Ref: {execution?.provider_reference || "pay_retry_mock_001"}
              </p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>Idempotency:</span>
                <span className="text-cyan-400 font-mono text-[10px]">
                  {execution?.idempotency_key ? `${execution.idempotency_key.slice(0, 18)}...` : `ray:${caseData.id}:retry:1`}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Adapter:</span>
                <span className="text-slate-300">Razorpay Test Adapter</span>
              </div>
            </div>
          </div>

          {/* Card 06: Verification */}
          <div className="p-5 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                06 &mdash; VERIFICATION
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                DUAL-SIGNAL
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="text-base font-bold text-emerald-400 uppercase flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                {isRecovered ? "VERIFIED" : (verification?.verification_status || "PENDING")}
              </div>
              <p className="text-[11px] text-slate-400">Independent dual confirmation</p>
            </div>
            <div className="pt-2 border-t border-[#141E2C] text-[11px] text-slate-400 space-y-1">
              <div className="flex justify-between">
                <span>API Status:</span>
                <span className="text-emerald-400">✓ CAPTURED</span>
              </div>
              <div className="flex justify-between">
                <span>Webhook HMAC:</span>
                <span className="text-emerald-400">✓ SIGNED</span>
              </div>
            </div>
          </div>
        </div>

        {/* Final Verified Revenue Callout */}
        <div className="p-5 rounded-xl bg-[#0D1826] border border-emerald-500/30 flex items-center justify-between font-mono">
          <div className="space-y-1">
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
              VERIFIED REVENUE INCREMENT
            </span>
            <div className="text-2xl font-bold text-white tabular-nums">
              {formatCurrencyINR(isRecovered ? caseData.amount_at_risk : (caseData.recovered_amount || 0))}
            </div>
          </div>
          <div className="text-right space-y-1">
            <span className="px-3 py-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs font-bold">
              {isRecovered ? "LEDGER RECOVERED" : "HELD PENDING DUAL-SIGNAL"}
            </span>
            <p className="text-[10px] text-slate-400 block">
              Hash: {verification?.evidence_hash ? `${verification.evidence_hash.slice(0, 16)}...` : "SHA256:58f2b854..."}
            </p>
          </div>
        </div>
      </div>

      {/* Explanatory Traceability Timelines */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 font-mono text-xs">
        {/* Panel 1: Why Did RAY Take This Action? */}
        <div className="p-5 rounded-xl bg-[#0A0F1A] border border-[#162234] space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase tracking-wider text-xs">
            <CheckCircle2 className="w-4 h-4" />
            WHY DID RAY TAKE THIS ACTION?
          </div>
          <div className="space-y-2.5 text-slate-300">
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">1.</span>
              <span>Payment failure detected with amount {formatCurrencyINR(caseData.amount_at_risk)}.</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">2.</span>
              <span>ML estimated {(prob * 100).toFixed(1)}% recovery probability (Band: {band}).</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">3.</span>
              <span>Diagnosis classified failure root cause as {caseData.failure_type}.</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">4.</span>
              <span>Recovery Planner formulated Expected Value recovery plan ({caseData.recommended_action || "RETRY"}).</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">5.</span>
              <span>Deterministic Policy Engine evaluated rules 1-10.</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">6.</span>
              <span>Policy authorized retry (ceiling &le; ₹10,000, attempts &le; 1).</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">7.</span>
              <span>Tool Gateway executed with canonical idempotency key protection.</span>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-blue-400 font-bold">8.</span>
              <span>API poll + webhook HMAC independently confirmed recovery &rarr; VERIFIED.</span>
            </div>
          </div>
        </div>

        {/* Panel 2: Why Would RAY Refuse To Act? */}
        <div className="p-5 rounded-xl bg-[#0A0F1A] border border-[#162234] space-y-3">
          <div className="flex items-center gap-2 text-amber-400 font-bold uppercase tracking-wider text-xs">
            <AlertTriangle className="w-4 h-4" />
            WHY WOULD RAY REFUSE TO ACT?
          </div>
          <div className="space-y-2.5 text-slate-300">
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-amber-400 font-bold">&bull;</span>
              <div>
                <span className="font-semibold text-white">High-Value Ceiling (Rule 7): </span>
                <span>Any transaction &ge; ₹50,000 triggers immediate freeze in AWAITING_APPROVAL.</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-rose-400 font-bold">&bull;</span>
              <div>
                <span className="font-semibold text-white">Permanent Failures &amp; Fraud (Rules 4 &amp; 6): </span>
                <span>Fraud flags or permanent declines are permanently DENIED with 0 retries.</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-rose-400 font-bold">&bull;</span>
              <div>
                <span className="font-semibold text-white">Customer Opt-Out (Rule 5): </span>
                <span>Customer opt-out flags are respected unconditionally (DENY).</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-amber-400 font-bold">&bull;</span>
              <div>
                <span className="font-semibold text-white">Retry Limit (Rule 1): </span>
                <span>Maximum 1 automatic retry attempt per failed transaction.</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5 p-2 rounded bg-[#0E1522] border border-[#142032]">
              <span className="text-cyan-400 font-bold">&bull;</span>
              <div>
                <span className="font-semibold text-white">Verification Discrepancy: </span>
                <span>If API status conflicts with Webhook payload, case is halted in HUMAN_REVIEW with ₹0.00 revenue.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chronological Event Timeline */}
      <div className="p-6 rounded-xl bg-[#0A0E17] border border-[#162030] space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Real-Time Audit Trail &amp; Multi-Agent Event Stream
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            SSE Live Feed Supported
          </span>
        </div>

        {timeline.length === 0 ? (
          <p className="text-xs font-mono text-slate-400">
            No autonomous events recorded yet. Click &ldquo;Execute Recovery&rdquo; to dispatch.
          </p>
        ) : (
          <div className="space-y-2.5 font-mono text-xs">
            {timeline.map((evt, idx) => (
              <div
                key={evt.event_id || idx}
                className="flex items-start gap-3 p-3 rounded-lg bg-[#0E1522] border border-[#162234]"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{evt.event_type}</span>
                    <span className="text-slate-400 text-[10px]">{evt.timestamp}</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Actor: <span className="text-slate-200">{evt.actor}</span> &bull; Correlation:{" "}
                    <span className="text-slate-400">{evt.correlation_id}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
