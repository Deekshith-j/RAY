"use client";

import React from "react";
import {
  ShieldCheck,
  Lock,
  Terminal,
  UserCheck,
  RotateCcw,
  KeyRound,
  FileCheck2,
  ShieldAlert,
  Hash,
  CheckCircle2,
} from "lucide-react";

const securityItems = [
  {
    title: "Deterministic Policy Isolation",
    status: "ENFORCED",
    icon: Lock,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "Policy rules are hardcoded in deterministic Python. The LLM and ML models are strictly advisory and cannot alter thresholds, bypass retry ceilings, or grant financial authorizations.",
    component: "app.core.policy_engine.PolicyEngine",
  },
  {
    title: "Tool Gateway Boundary",
    status: "ENFORCED",
    icon: Terminal,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "All financial operations must route through the Tool Gateway. Direct agent calls to Razorpay APIs are architecturally impossible; calls fail closed if authorization records are missing.",
    component: "app.tools.gateway.ToolGateway",
  },
  {
    title: "Mandatory Human Approval Gate",
    status: "ACTIVE",
    icon: UserCheck,
    badgeColor: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    description:
      "Transactions at or above ₹50,000 immediately trigger a hard policy freeze in AWAITING_APPROVAL. An immutable HumanApprovalRecord signed by an authorized operator is required before tool execution.",
    component: "Policy Rule 7 (≥ ₹50,000)",
  },
  {
    title: "Canonical Idempotency Protection",
    status: "ENFORCED",
    icon: RotateCcw,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "Structured key ray:{case_id}:{strategy}:{attempt_number} guarantees at-most-once execution. Network retries return cached responses (is_idempotent_replay = True) without duplicate charges.",
    component: "app.tools.idempotency.IdempotencyManager",
  },
  {
    title: "HMAC-SHA256 Webhook Verification",
    status: "ACTIVE",
    icon: KeyRound,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "All inbound Razorpay webhooks are cryptographically authenticated via HMAC-SHA256 against x-razorpay-signature using timing-safe comparison to prevent forgery and replay attacks.",
    component: "app.core.security.verify_webhook_signature",
  },
  {
    title: "Dual-Signal Verification Agreement",
    status: "ACTIVE",
    icon: FileCheck2,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "Independent API-state confirmation + Razorpay webhook confirmation must agree on payment identity and captured state. Conflicting signals escalate to HUMAN_REVIEW with ₹0.00 revenue counted.",
    component: "app.verification.engine.VerificationEngine",
  },
  {
    title: "Prompt Injection Containment",
    status: "ACTIVE",
    icon: ShieldAlert,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "All untrusted customer free-text (notes, failure descriptions, customer names) are wrapped in <UNTRUSTED_DATA> boundaries and evaluated as passive data, neutralizing jailbreaks.",
    component: "app.agents.base.PromptInjectionDefense",
  },
  {
    title: "Tamper-Evident Evidence Provenance",
    status: "ACTIVE",
    icon: Hash,
    badgeColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    description:
      "Cryptographic SHA-256 evidence hashing tracks API responses and webhook payloads across the entire lifecycle: Prediction → Decision → Authorization → Execution → Verification.",
    component: "app.models.entities.VerificationRecord",
  },
];

export default function SecurityPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <ShieldCheck className="w-6 h-6 text-emerald-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">System Security &amp; Safety Controls</h1>
        </div>
        <p className="text-sm text-slate-400">
          Defense-in-depth architecture enforcing deterministic financial boundaries around AI advisory agents.
        </p>
      </div>

      {/* Core Invariant Banner */}
      <div className="p-5 rounded-xl bg-[#0D1524] border border-[#1E2D44] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            Core System Invariant Active
          </div>
          <p className="text-xs text-slate-300 font-mono">
            PREDICTION ≠ RECOMMENDATION ≠ AUTHORIZATION ≠ EXECUTION ≠ VERIFICATION ≠ VERIFIED_REVENUE
          </p>
          <p className="text-xs text-slate-400">
            AI intelligence is architecturally isolated from financial execution authority.
          </p>
        </div>
        <span className="px-3 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold shrink-0 self-start md:self-center">
          100% COVERAGE
        </span>
      </div>

      {/* Security Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {securityItems.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className="p-5 rounded-xl bg-[#0A0F1A] border border-[#162234] hover:border-[#223550] transition-colors space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#111A29] border border-[#1D2C42] flex items-center justify-center text-slate-200">
                    <Icon className="w-4 h-4 text-emerald-400" />
                  </div>
                  <h3 className="font-semibold text-sm text-white">{item.title}</h3>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${item.badgeColor}`}
                >
                  {item.status}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{item.description}</p>

              <div className="pt-2 border-t border-[#141E2E] flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Enforcing Module:</span>
                <span className="text-slate-300 truncate max-w-[240px]">{item.component}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
