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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Layers className="w-6 h-6 text-emerald-400" />
            Revenue Recovery Cases
          </h2>
          <p className="text-sm text-slate-400">
            Real-time ledger of all detected payment anomalies, AI diagnoses, and verification statuses.
          </p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 text-xs font-semibold text-slate-300 hover:bg-slate-700 transition"
        >
          <RotateCw className="w-3.5 h-3.5" />
          Refresh Cases
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-[#0B1120] border border-slate-800 flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Case ID, customer name, or failure type..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="py-2 px-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="">All States</option>
            <option value="ANALYZING">ANALYZING</option>
            <option value="AWAITING_APPROVAL">AWAITING_APPROVAL</option>
            <option value="EXECUTING">EXECUTING</option>
            <option value="AWAITING_VERIFICATION">AWAITING_VERIFICATION</option>
            <option value="RECOVERED">RECOVERED</option>
            <option value="STOPPED">STOPPED</option>
            <option value="FAILED_RECOVERY">FAILED_RECOVERY</option>
          </select>
        </div>
      </div>

      {/* Cases Table */}
      <div className="rounded-xl bg-[#0B1120] border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th className="px-5 py-3">Case ID</th>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Amount at Risk</th>
                <th className="px-5 py-3">Recoverability</th>
                <th className="px-5 py-3">Expected Value</th>
                <th className="px-5 py-3">Failure Type</th>
                <th className="px-5 py-3">Recommended Strategy</th>
                <th className="px-5 py-3">Current State</th>
                <th className="px-5 py-3">Verified Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-5 py-12 text-center text-slate-500">
                    <RotateCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-500" />
                    Loading recovery cases...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-5 py-12 text-center text-slate-500">
                    No cases match the current filter.
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="px-5 py-3.5 font-mono font-semibold">
                      <Link
                        href={`/cases/${c.id}`}
                        className="text-emerald-400 hover:text-emerald-300 hover:underline flex items-center gap-1.5"
                      >
                        {c.id.slice(0, 16)}
                        <Eye className="w-3 h-3 opacity-60" />
                      </Link>
                    </td>
                    <td className="px-5 py-3.5 font-medium text-white">{c.customer_name || c.customer_id}</td>
                    <td className="px-5 py-3.5 font-semibold text-white">{formatCurrencyINR(c.amount_at_risk)}</td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2">
                        <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${
                              c.recoverability_score > 0.7
                                ? "bg-emerald-500"
                                : c.recoverability_score > 0.4
                                ? "bg-amber-500"
                                : "bg-rose-500"
                            }`}
                            style={{ width: `${c.recoverability_score * 100}%` }}
                          />
                        </div>
                        <span className="font-semibold">{(c.recoverability_score * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-blue-400">
                      {formatCurrencyINR(c.expected_recovery_value)}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-slate-400">{c.failure_type}</td>
                    <td className="px-5 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-200 border border-slate-700">
                        {c.recommended_action || "NONE"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          c.state === "RECOVERED"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : c.state === "AWAITING_APPROVAL"
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : c.state === "ANALYZING"
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {c.state}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 font-bold text-emerald-400">
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
