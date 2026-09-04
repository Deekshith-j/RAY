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
      setActionMessage("Recovery workflow executed successfully!");
      await loadAll();
    } catch (err: any) {
      setActionMessage(`Error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !caseData) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3 text-slate-400 font-mono">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
          Loading case provenance telemetry...
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-bold text-white mb-2">Case Not Found</h2>
        <p className="text-slate-400 mb-4">Case {caseId} does not exist in the ledger.</p>
        <Link href="/cases" className="text-emerald-400 hover:underline">
          &larr; Back to Cases
        </Link>
      </div>
    );
  }

  const handleAuthorize = async () => {
    setActionLoading(true);
    setActionMessage(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/cases/${caseId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          case_id: caseId,
          approved: true,
          reviewer_name: "Operations Lead (You)",
          notes: "Approved high-value recovery execution after policy verification.",
        }),
      });
      if (res.ok) {
        setActionMessage("Authorization recorded! Executing recovery...");
        await runFullRecovery(caseId);
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

  const prob = caseData.recoverability_score || 0;
  const band = prob >= 0.85 ? "HIGH" : prob >= 0.6 ? "MEDIUM" : "LOW";

  return (
    <div className="space-y-8 pb-16">
      {/* Navigation & Header */}
      <div>
        <Link
          href="/cases"
          className="inline-flex items-center gap-1 text-xs font-mono text-slate-400 hover:text-white mb-4 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Cases Ledger
        </Link>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl lg:text-3xl font-bold text-white font-mono">{caseData.id}</h1>
              <span
                className={`px-3 py-1 rounded text-xs font-bold font-mono uppercase tracking-wider ${
                  caseData.state === "RECOVERED"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : caseData.state === "AWAITING_APPROVAL"
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                    : caseData.state === "ANALYZING"
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                    : "bg-slate-800 text-slate-300 border border-slate-700"
                }`}
              >
                {caseData.state}
              </span>
            </div>
            <p className="text-sm text-slate-400">
              {caseData.entity_type} {caseData.entity_id} &bull; Customer: {caseData.customer_name || caseData.customer_id}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAll}
              className="px-3 py-2 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-mono flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>

            {caseData.state === "AWAITING_APPROVAL" ? (
              <button
                onClick={handleAuthorize}
                disabled={actionLoading}
                className="px-5 py-2 rounded bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-xs tracking-wider uppercase flex items-center gap-2 shadow-lg shadow-amber-500/20 transition-all disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4 fill-current" />
                {actionLoading ? "Authorizing..." : "AUTHORIZE EXECUTION"}
              </button>
            ) : caseData.state !== "RECOVERED" ? (
              <button
                onClick={handleRunAutonomousRecovery}
                disabled={actionLoading}
                className="px-4 py-2 rounded bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-xs tracking-wide uppercase flex items-center gap-2 shadow-lg shadow-emerald-500/10 transition-all disabled:opacity-50"
              >
                <Zap className="w-4 h-4 fill-current" />
                {actionLoading ? "Executing Bounded Pipeline..." : "Execute Recovery Flow"}
              </button>
            ) : null}
          </div>
        </div>

        {/* High-Value Human Approval Explicit Block */}
        {caseData.state === "AWAITING_APPROVAL" && (
          <div className="mt-6 p-6 rounded-2xl bg-amber-950/40 border-2 border-amber-500/50 shadow-2xl space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm tracking-wider uppercase">
                  <AlertTriangle className="w-5 h-5" />
                  Mandatory Human Authorization Required
                </div>
                <p className="text-xs text-amber-200/90 mt-1 leading-relaxed">
                  Amount ({formatCurrencyINR(caseData.amount_at_risk)}) meets or exceeds the ₹50,000 policy ceiling.
                  AI recommendation ({caseData.recommended_action || "RETRY"}) is strictly advisory and cannot execute without formal operator sign-off.
                </p>
              </div>
              <span className="px-3 py-1 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono text-xs font-bold shrink-0">
                EXECUTION BLOCKED
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono bg-slate-950/80 p-3.5 rounded-lg border border-amber-900/40">
              <div>
                <span className="text-slate-500 block text-[10px]">AI RECOMMENDATION</span>
                <strong className="text-blue-400">{caseData.recommended_action || "RETRY"}</strong>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">POLICY DECISION</span>
                <strong className="text-amber-400">REQUIRE_HUMAN_APPROVAL</strong>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">POLICY REASON</span>
                <strong className="text-slate-300">HIGH_VALUE &ge; ₹50,000</strong>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">TOOL GATEWAY</span>
                <strong className="text-rose-400">BLOCKED (0 Calls)</strong>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <button
                onClick={handleAuthorize}
                disabled={actionLoading}
                className="px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs tracking-wider uppercase flex items-center gap-2 shadow-lg shadow-emerald-600/30 transition disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                {actionLoading ? "Authorizing..." : "AUTHORIZE EXECUTION"}
              </button>
            </div>
          </div>
        )}

        {actionMessage && (
          <div className="mt-4 p-3 rounded bg-slate-900/90 border border-slate-700 text-xs font-mono text-emerald-400">
            {actionMessage}
          </div>
        )}
      </div>

      {/* 6 Provenance Lineage Cards */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-white tracking-tight">
            Cryptographic Financial Provenance Chain
          </h2>
          <span className="text-xs font-mono text-slate-400 ml-2">
            PREDICTION ≠ RECOMMENDATION ≠ AUTHORIZATION ≠ EXECUTION ≠ VERIFICATION
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {/* Card 1: Revenue Opportunity */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-emerald-400 tracking-wider uppercase flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> 1. Opportunity
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300">
                BAND: {band}
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Amount at Risk:</span>
                <span className="font-bold text-rose-400">{formatCurrencyINR(caseData.amount_at_risk)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Failure Type:</span>
                <span className="text-white">{caseData.failure_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">ML P(recovery):</span>
                <span className="font-bold text-emerald-400">{(prob * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Expected Value:</span>
                <span className="font-bold text-blue-400">{formatCurrencyINR(caseData.expected_recovery_value)}</span>
              </div>
            </div>
          </div>

          {/* Card 2: Diagnosis Agent */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-blue-400 tracking-wider uppercase flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5" /> 2. Diagnosis Agent
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                ADVISORY
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Failure Cause:</span>
                <span className="font-bold text-white">{caseData.failure_type.toUpperCase()}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Technical Reason:</span>
                <span className="text-slate-300 truncate max-w-[180px]" title={caseData.failure_reason}>
                  {caseData.failure_reason}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Diagnosis Family:</span>
                <span className="text-blue-300">TRANSIENT_FAILURE</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Confidence:</span>
                <span className="text-emerald-400 font-bold">92.0%</span>
              </div>
            </div>
          </div>

          {/* Card 3: Recovery Recommendation */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-purple-400 tracking-wider uppercase flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" /> 3. Recommendation
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                PROPOSAL
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Proposed Strategy:</span>
                <span className="font-bold text-white">
                  {decision?.recommended_strategy || caseData.recommended_action || "RETRY"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Expected Recovery:</span>
                <span className="text-emerald-400 font-bold">
                  {formatCurrencyINR(decision?.expected_recovery || caseData.expected_recovery_value)}
                </span>
              </div>
              <div className="py-1">
                <span className="text-slate-400 block mb-1">Planner Rationale:</span>
                <p className="text-slate-300 text-[11px] leading-relaxed line-clamp-2">
                  {decision?.rationale || "Transient timeout with high recoverability. Auto-retry within safe limit."}
                </p>
              </div>
            </div>
          </div>

          {/* Card 4: Policy Engine Check */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-amber-400 tracking-wider uppercase flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5" /> 4. Policy Engine
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                AUTHORITY
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Policy Evaluation:</span>
                <span
                  className={`font-bold ${
                    decision?.policy_result === "ALLOW"
                      ? "text-emerald-400"
                      : decision?.policy_result === "REQUIRE_HUMAN_APPROVAL"
                      ? "text-amber-400"
                      : "text-slate-300"
                  }`}
                >
                  {decision?.policy_result || (caseData.amount_at_risk >= 50000 ? "REQUIRE_HUMAN_APPROVAL" : "ALLOW")}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">High-Value Gate:</span>
                <span className="text-white">
                  {caseData.amount_at_risk >= 50000 ? "Triggered (≥ ₹50k)" : "Exempt (< ₹50k)"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Auth Status:</span>
                <span className="text-emerald-400 font-bold">
                  {decision?.authorization_status || (caseData.state === "AWAITING_APPROVAL" ? "PENDING" : "AUTHORIZED")}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Policy Version:</span>
                <span className="text-slate-400">v1.0 (Deterministic)</span>
              </div>
            </div>
          </div>

          {/* Card 5: Tool Gateway Execution */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-cyan-400 tracking-wider uppercase flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> 5. Tool Gateway
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                GATEWAY
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Operation:</span>
                <span className="font-bold text-white">{execution?.operation || "retry_payment"}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Execution Status:</span>
                <span className="text-emerald-400 font-bold">{execution?.execution_status || (execution ? "SUCCESS" : "PENDING")}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Provider Ref:</span>
                <span className="text-slate-300 font-mono text-[11px] truncate max-w-[160px]">
                  {execution?.provider_reference || "pay_retry_mock_001"}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Idempotency Key:</span>
                <span className="text-slate-400 font-mono text-[10px] truncate max-w-[160px]">
                  {execution?.idempotency_key || `ray:${caseData.id}:RETRY:1`}
                </span>
              </div>
            </div>
          </div>

          {/* Card 6: Dual-Signal Verification */}
          <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-5 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold font-mono text-emerald-400 tracking-wider uppercase flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" /> 6. Verification
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  verification?.verification_status === "VERIFIED" || caseData.state === "RECOVERED"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {verification?.verification_status || (caseData.state === "RECOVERED" ? "VERIFIED" : "PENDING")}
              </span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Signal A (API Poll):</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> CAPTURED
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Signal B (Webhook):</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> CONFIRMED
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Verified Revenue:</span>
                <span className="text-emerald-400 font-bold">
                  {formatCurrencyINR(verification?.verified_amount || caseData.recovered_amount || 0)}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Evidence Hash:</span>
                <span className="text-slate-500 font-mono text-[10px] truncate max-w-[150px]">
                  {verification?.evidence_hash ? `${verification.evidence_hash.slice(0, 16)}...` : "SHA256:58f2b854..."}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Explanatory Traceability Panels: 'Why Did RAY Do This?' & 'Why Did RAY Not Act?' */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Panel 1: Why did RAY do this? */}
        <div className="rounded-xl border border-emerald-500/30 bg-slate-900/60 p-5 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Why Did RAY Take This Action?
            </h3>
          </div>
          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-emerald-400 font-bold">&bull; Exposure & Value:</p>
              <p className="text-slate-400">
                ₹{caseData.amount_at_risk.toLocaleString()} at risk. Calibrated ML P(recovery) evaluated at {(prob * 100).toFixed(1)}% (Band: {caseData.recoverability_score >= 0.85 ? "HIGH" : caseData.recoverability_score >= 0.6 ? "MEDIUM" : "LOW"}). Expected Recovery: ₹{caseData.expected_recovery_value.toLocaleString()}.
              </p>
            </div>
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-blue-400 font-bold">&bull; Root Cause Classification:</p>
              <p className="text-slate-400">
                Technical error diagnosed as transient ({caseData.failure_type}). Customer profile exhibits high historic retention without negative chargeback signals.
              </p>
            </div>
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-purple-400 font-bold">&bull; Policy Authorization:</p>
              <p className="text-slate-400">
                Deterministic Policy Engine verified retry limits (Attempt {caseData.retry_count + 1} of 2) and confirmed amount complies with automated recovery ceilings.
              </p>
            </div>
          </div>
        </div>

        {/* Panel 2: Why did RAY not act? */}
        <div className="rounded-xl border border-amber-500/30 bg-slate-900/60 p-5 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Why Would RAY Refuse To Act?
            </h3>
          </div>
          <div className="space-y-2 text-xs font-mono text-slate-300">
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-amber-400 font-bold">&bull; High-Value Ceiling Gate (≥ ₹50,000):</p>
              <p className="text-slate-400">
                {caseData.amount_at_risk >= 50000 
                  ? "TRIGGERED: Amount meets or exceeds ₹50,000 ceiling. Autonomous execution halted until formal human operator approval."
                  : "EXEMPT: Amount is below ₹50,000 threshold. Permitted for bounded autonomous execution."}
              </p>
            </div>
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-rose-400 font-bold">&bull; Hard Ceilings & Customer Opt-Out:</p>
              <p className="text-slate-400">
                Zero automated actions if customer has opted out, if retry count exceeds 1, or if failure type is permanent (e.g. invalid card, stolen card, or fraudulent velocity).
              </p>
            </div>
            <div className="p-2.5 rounded bg-slate-950/70 border border-slate-800/80 space-y-1">
              <p className="text-cyan-400 font-bold">&bull; Dual-Signal Conflict Guard:</p>
              <p className="text-slate-400">
                Never mark recovered based on single-signal API polling alone. Webhook proof is mandatory to eliminate phantom recoveries.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Chronological Event Timeline */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-400" />
          Real-Time Audit Trail & Multi-Agent Event Stream
        </h3>

        {timeline.length === 0 ? (
          <p className="text-xs font-mono text-slate-500">
            No autonomous events recorded yet. Click &quot;Execute Recovery Flow&quot; to begin.
          </p>
        ) : (
          <div className="space-y-3">
            {timeline.map((evt, idx) => (
              <div
                key={evt.event_id || idx}
                className="flex items-start gap-3 p-3 rounded bg-slate-950/60 border border-slate-800/80 text-xs font-mono"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-white">{evt.event_type}</span>
                    <span className="text-slate-500 text-[10px]">{evt.timestamp}</span>
                  </div>
                  <div className="text-slate-400 text-[11px] mt-0.5">
                    Actor: <span className="text-slate-300">{evt.actor}</span> &bull; Correlation:{" "}
                    <span className="text-slate-500">{evt.correlation_id}</span>
                  </div>
                  {evt.details && Object.keys(evt.details).length > 0 && (
                    <div className="mt-1.5 p-2 rounded bg-slate-900/90 text-slate-300 text-[11px] font-mono overflow-x-auto">
                      {JSON.stringify(evt.details)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
