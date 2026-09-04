import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import {
  ShieldAlert,
  Activity,
  Layers,
  CheckCircle2,
  Sliders,
  TrendingUp,
  Cpu,
  BarChart3,
} from "lucide-react";

export const metadata: Metadata = {
  title: "RAY — Autonomous Revenue Recovery & Verification Engine",
  description: "Closed-loop AI Revenue Recovery for Razorpay Buildathon",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090D16] text-slate-100 flex antialiased">
        {/* Sidebar */}
        <aside className="w-64 border-r border-slate-800/80 bg-[#0B1120] flex flex-col justify-between p-4 shrink-0">
          <div>
            {/* Logo */}
            <div className="flex items-center gap-3 px-2 py-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Cpu className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg tracking-wider text-white flex items-center gap-1.5">
                  RAY
                  <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    Engine
                  </span>
                </h1>
                <p className="text-[11px] text-slate-400 font-medium">Razorpay AI Autonomy</p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="space-y-1">
              <Link
                href="/"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-200 hover:bg-slate-800/60 hover:text-white transition-colors"
              >
                <Activity className="w-4 h-4 text-blue-400" />
                Financial Overview
              </Link>
              <Link
                href="/cases"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-slate-800/60 hover:text-white transition-colors"
              >
                <Layers className="w-4 h-4 text-emerald-400" />
                Recovery Cases
              </Link>
              <Link
                href="/approvals"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-slate-800/60 hover:text-white transition-colors"
              >
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Human Approvals
              </Link>
              <Link
                href="/simulator"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-slate-800/60 hover:text-white transition-colors"
              >
                <Sliders className="w-4 h-4 text-purple-400" />
                Failure Simulator
              </Link>
              <Link
                href="/analytics"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:bg-slate-800/60 hover:text-white transition-colors"
              >
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                Analytics & Audit
              </Link>
            </nav>
          </div>

          {/* Verification Badge */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
            <div className="flex items-center gap-2 mb-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span className="font-semibold text-slate-200">Verified Outcomes Only</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Revenue counts exclusively after cryptographically verified Razorpay webhooks.
            </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          <header className="h-16 border-b border-slate-800/80 bg-[#0B1120]/60 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-10">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Razorpay Test Mode Active
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">
                Policy Engine: <strong className="text-emerald-400">Strict Deterministic</strong>
              </span>
              <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">
                Max Retry: <strong className="text-blue-400">₹10,000</strong>
              </span>
              <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700">
                Approval: <strong className="text-amber-400">&ge; ₹50,000</strong>
              </span>
            </div>
          </header>

          <div className="p-8 max-w-7xl w-full mx-auto space-y-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
