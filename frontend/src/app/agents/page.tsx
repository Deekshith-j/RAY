"use client";

import React from "react";
import {
  Bot,
  Cpu,
  Lock,
  Terminal,
  ShieldCheck,
  CheckCircle2,
  Activity,
  Layers,
  Sparkles,
} from "lucide-react";

const agentsList = [
  {
    name: "Revenue Detective",
    role: "Advisory / Read-Only",
    nature: "AI AGENT",
    natureBadge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    status: "READY",
    icon: Bot,
    description:
      "Extracts failure telemetry, computes customer risk profile, and evaluates financial recovery exposure. Has strictly zero tool execution permissions.",
    inputs: "Case ID, Ground-Truth Amount, Customer History",
    outputs: "RevenueOpportunity (Pydantic)",
  },
  {
    name: "Recoverability ML",
    role: "Calibrated Probability Model",
    nature: "STATISTICAL ML",
    natureBadge: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    status: "ACTIVE",
    icon: Cpu,
    description:
      "Sigmoid-calibrated Logistic Regression estimating P(recovery). Ground-truth held-out metrics: PR-AUC 0.8602, Brier 0.1372, Revenue-Weighted Recall 95.0%.",
    inputs: "Normalized transaction features",
    outputs: "P(recovery), Recoverability Band, Expected Recovery",
  },
  {
    name: "Diagnosis Agent",
    role: "Root Cause Telemetry",
    nature: "AI AGENT",
    natureBadge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    status: "READY",
    icon: Activity,
    description:
      "Classifies failure root cause into standardized categories (TRANSIENT, TIMEOUT, BANK_UNAVAILABLE, etc.). Treats all customer-supplied text as untrusted data.",
    inputs: "Sanitized failure telemetry (<UNTRUSTED_DATA>)",
    outputs: "DiagnosisResult (Pydantic)",
  },
  {
    name: "Recovery Planner",
    role: "Expected Value Optimization",
    nature: "AI AGENT",
    natureBadge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    status: "READY",
    icon: Sparkles,
    description:
      "Evaluates candidate actions (RETRY, PAYMENT_LINK, SUBSCRIPTION_RECOVERY) based on EV = P(success) * Amount - ActionCost - RiskPenalty. Cannot execute or authorize.",
    inputs: "DiagnosisResult, Customer Tier, Financial Amount",
    outputs: "RecoveryPlan with ranked candidate strategies",
  },
  {
    name: "Deterministic Policy Engine",
    role: "Sole Financial Authority",
    nature: "DETERMINISTIC CONTROL",
    natureBadge: "bg-amber-500/15 text-amber-300 border-amber-500/30 font-black",
    status: "ACTIVE AUTHORITY",
    icon: Lock,
    isAuthority: true,
    description:
      "NOT AN LLM. Hardcoded deterministic Python rules governing all financial authorizations. Enforces auto-retry ceilings (<= ₹10,000), retry limits (<= 1), fraud vetoes, and mandatory human approval (>= ₹50,000).",
    inputs: "RecoveryCase ground truth, Proposed Strategy",
    outputs: "PolicyDecision (ALLOW, DENY, REQUIRE_HUMAN_APPROVAL)",
  },
  {
    name: "Tool Gateway",
    role: "Execution Choke Point",
    nature: "ENFORCED GATEWAY",
    natureBadge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    status: "ACTIVE",
    icon: Terminal,
    description:
      "The single bridge between agents and payment adapters. Validates Policy authorization, operator sign-offs, and canonical idempotency (ray:{case_id}:{strategy}:{attempt_number}).",
    inputs: "ToolCallRequest with decision & authorization IDs",
    outputs: "ToolCallResult, Cached Replay Flag, Provider Reference",
  },
  {
    name: "Execution Agent",
    role: "Tool Gateway Mediator",
    nature: "BOUNDED RUNNER",
    natureBadge: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    status: "READY",
    icon: Layers,
    description:
      "Translates approved recovery strategies into structured Tool Gateway calls. Has ZERO direct access to Razorpay credentials or payment APIs.",
    inputs: "Authorized RecoveryDecision",
    outputs: "ToolGateway.execute() dispatch",
  },
  {
    name: "Verification Engine",
    role: "Independent Dual-Signal Prover",
    nature: "VERIFICATION ENGINE",
    natureBadge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    status: "ACTIVE",
    icon: ShieldCheck,
    description:
      "Independently confirms financial outcomes using Signal A (API polling) + Signal B (HMAC-SHA256 authenticated webhook). Grants VERIFIED only when both signals agree.",
    inputs: "Case ID, Execution ID, Webhook Event Payload",
    outputs: "VerificationResult, Evidence Hashes, Verified Revenue Increment",
  },
];

export default function AgentActivityPage() {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Bot className="w-6 h-6 text-blue-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">Bounded Agentic Fleet Architecture</h1>
        </div>
        <p className="text-sm text-slate-400">
          Architecture overview of advisory AI agents, deterministic controls, and verification boundaries.
        </p>
      </div>

      {/* Critical Architecture Invariant Box */}
      <div className="p-5 rounded-xl bg-[#0D1524] border border-[#1C2C44] space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-blue-400 flex items-center gap-2">
            <Lock className="w-4 h-4 text-amber-400" />
            Core Architectural Boundary
          </span>
          <span className="text-[11px] font-mono text-emerald-400 font-semibold">
            ADVISORY AI ≠ FINANCIAL AUTHORITY
          </span>
        </div>
        <p className="text-xs text-slate-300 font-mono">
          AI agents formulate hypotheses and recommend candidate actions. The deterministic Policy Engine holds 100% exclusive authority over execution permissions.
        </p>
      </div>

      {/* Fleet Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {agentsList.map((agent, idx) => {
          const Icon = agent.icon;
          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border transition-all ${
                agent.isAuthority
                  ? "bg-[#0E1624] border-amber-500/40 shadow-xl shadow-amber-950/10"
                  : "bg-[#0A0F1A] border-[#162234] hover:border-[#223550]"
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center border ${
                      agent.isAuthority
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                        : "bg-[#111A29] border-[#1D2C42] text-slate-300"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm text-white">{agent.name}</h3>
                    <p className="text-[11px] text-slate-400 font-mono">{agent.role}</p>
                  </div>
                </div>

                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono border ${agent.natureBadge}`}
                >
                  {agent.nature}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed mb-4">{agent.description}</p>

              <div className="pt-3 border-t border-[#141E2E] space-y-1.5 text-[11px] font-mono">
                <div className="flex justify-between text-slate-400">
                  <span>Inputs:</span>
                  <span className="text-slate-300 truncate max-w-[220px]">{agent.inputs}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Outputs:</span>
                  <span className="text-emerald-400 font-semibold truncate max-w-[220px]">{agent.outputs}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
