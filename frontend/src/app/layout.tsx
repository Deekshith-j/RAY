import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { Lock, ShieldCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "RAY — Revenue Autonomy Engine",
  description: "Controlled Agentic Revenue Recovery for Razorpay AI Buildathon",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#080C14] text-slate-100 flex antialiased">
        <Sidebar />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {/* Command Center Control Bar */}
          <header className="h-14 border-b border-[#161F2E] bg-[#0A0E17]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                RAZORPAY TEST MODE
              </span>
              <span className="text-[11px] font-mono text-slate-400 hidden lg:inline">
                Dual-Signal Verification Engine Active
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
              <div className="px-2.5 py-1 rounded bg-[#0D1420] border border-[#1C2738] flex items-center gap-1.5 text-[11px]">
                <Lock className="w-3 h-3 text-emerald-400" />
                <span>Policy Engine:</span>
                <strong className="text-emerald-300 font-semibold">Deterministic</strong>
              </div>
              <div className="px-2.5 py-1 rounded bg-[#0D1420] border border-[#1C2738] flex items-center gap-1.5 text-[11px] hidden sm:flex">
                <span>Auto-Retry:</span>
                <strong className="text-blue-300">&le; ₹10,000</strong>
              </div>
              <div className="px-2.5 py-1 rounded bg-[#0D1420] border border-[#1C2738] flex items-center gap-1.5 text-[11px] hidden md:flex">
                <span>Approval:</span>
                <strong className="text-amber-300">&ge; ₹50,000</strong>
              </div>
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
