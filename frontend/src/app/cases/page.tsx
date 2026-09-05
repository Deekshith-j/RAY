"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchCases, RecoveryCase } from "@/lib/api";
import { formatCurrencyINR } from "@/lib/formatters";
import {
  Layers,
  Search,
  Filter,
  RotateCw,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from "lucide-react";

export default function CasesPage() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [stateFilter, setStateFilter] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchCases({
        state: stateFilter || undefined,
        limit: 100,
      });
      setCases(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [stateFilter]);

  const filteredCases = cases.filter((c) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      c.id.toLowerCase().includes(term) ||
      (c.customer_name && c.customer_name.toLowerCase().includes(term)) ||
      c.failure_type.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#162030] pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Layers className="w-6 h-6 text-emerald-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">Revenue Recovery Cases Ledger</h1>
          </div>
          <p className="text-xs text-slate-400">
            Real-time ledger of all detected payment anomalies, AI diagnoses, and verification statuses.
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0E1624] border border-[#1C2C40] text-xs text-slate-300 hover:bg-[#142032] transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
          Refresh Cases
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0A0F1A] border border-[#162234] flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Case ID, customer name, or failure type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#0E1624] border border-[#1B273A] text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="py-2 px-3 rounded-lg bg-[#0E1624] border border-[#1B273A] text-xs text-slate-300 focus:outline-none focus:border-blue-500 font-mono"
          >
            <option value="">All States ({cases.length})</option>
            <option value="ANALYZING">ANALYZING</option>
            <option value="AWAITING_APPROVAL">AWAITING_APPROVAL</option>
            <option value="EXECUTING">EXECUTING</option>
            <option value="AWAITING_VERIFICATION">AWAITING_VERIFICATION</option>
            <option value="RECOVERED">RECOVERED</option>
            <option value="HUMAN_REVIEW">HUMAN_REVIEW</option>
            <option value="STOPPED">STOPPED</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="rounded-xl bg-[#0A0F1A] border border-[#162234] overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0D1524] text-slate-400 border-b border-[#162234] uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Amount at Risk</th>
                <th className="px-4 py-3">Recoverability</th>
                <th className="px-4 py-3">Expected Value</th>
                <th className="px-4 py-3">Failure Type</th>
                <th className="px-4 py-3">Strategy</th>
                <th className="px-4 py-3">Current State</th>
                <th className="px-4 py-3 text-right">Verified Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#131E2E] text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-slate-400">
                    <RotateCw className="w-4 h-4 animate-spin mx-auto mb-2 text-blue-400" />
                    Loading recovery cases...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center space-y-1">
                    <p className="text-xs font-semibold text-slate-300">No recovery cases found</p>
                    <p className="text-[11px] text-slate-400 font-mono">
                      RAY will surface revenue-at-risk opportunities as payment events arrive.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-[#0E1626] transition-colors">
                    <td className="px-4 py-3 font-bold whitespace-nowrap">
                      <Link
                        href={`/cases/${c.id}`}
                        className="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1.5"
                      >
                        {c.id}
                        <Eye className="w-3 h-3 opacity-60" />
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-300 whitespace-nowrap truncate max-w-[140px]">
                      {c.customer_name || c.customer_id}
                    </td>
                    <td className="px-4 py-3 font-bold tabular-nums text-white whitespace-nowrap">
                      {formatCurrencyINR(c.amount_at_risk)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-emerald-400 font-semibold tabular-nums">
                        {(c.recoverability_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold tabular-nums text-purple-300 whitespace-nowrap">
                      {formatCurrencyINR(c.expected_recovery_value)}
                    </td>
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap truncate max-w-[130px]">
                      {c.failure_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-[#111A29] text-slate-200 border border-[#1C2C44]">
                        {c.recommended_action || "RETRY"}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          c.state === "RECOVERED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : c.state === "AWAITING_APPROVAL"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : c.state === "HUMAN_REVIEW"
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                            : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        }`}
                      >
                        {c.state}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-bold tabular-nums text-emerald-400 text-right whitespace-nowrap">
                      {c.recovered_amount > 0 ? formatCurrencyINR(c.recovered_amount) : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
