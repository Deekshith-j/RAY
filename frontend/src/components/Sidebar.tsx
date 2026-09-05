"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Layers,
  ShieldAlert,
  Sliders,
  BarChart3,
  Bot,
  ScrollText,
  ShieldCheck,
  Cpu,
  Lock,
} from "lucide-react";

const mainNavItems = [
  { name: "Overview", href: "/", icon: Activity },
  { name: "Recovery Cases", href: "/cases", icon: Layers },
  { name: "Approvals", href: "/approvals", icon: ShieldAlert },
  { name: "Simulator", href: "/simulator", icon: Sliders },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
];

const systemNavItems = [
  { name: "Agent Activity", href: "/agents", icon: Bot },
  { name: "Audit Trail", href: "/audit", icon: ScrollText },
  { name: "Security", href: "/security", icon: ShieldCheck },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-[#1B2433] bg-[#0A0E17] flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="px-5 py-5 border-b border-[#161F2E]">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:border-blue-400/50 transition-colors">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">RAY</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                  v2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium leading-none mt-0.5">
                Revenue Autonomy Engine
              </p>
            </div>
          </Link>
        </div>

        {/* Primary Navigation */}
        <div className="px-3 py-4 space-y-6">
          <div>
            <div className="space-y-0.5">
              {mainNavItems.map((item) => {
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(item.href);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-[#162032] text-white border border-[#23334D]/60 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-[#121926]"
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-blue-400" : "text-slate-400"
                      }`}
                    />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* System Navigation Section */}
          <div>
            <div className="px-3 mb-2">
              <span className="text-[10px] font-bold font-mono uppercase tracking-wider text-slate-400">
                SYSTEM
              </span>
            </div>
            <div className="space-y-0.5">
              {systemNavItems.map((item) => {
                const isActive = pathname.startsWith(item.href);
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? "bg-[#162032] text-white border border-[#23334D]/60 shadow-sm"
                        : "text-slate-400 hover:text-slate-200 hover:bg-[#121926]"
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-emerald-400" : "text-slate-400"
                      }`}
                    />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-[#161F2E] bg-[#070A10]/60 space-y-2 text-xs font-mono">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            System Status
          </span>
          <span className="flex items-center gap-1.5 text-emerald-400 text-[11px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Operational
          </span>
        </div>

        <div className="p-2.5 rounded bg-[#0D1420] border border-[#1B2636] space-y-1 text-[11px]">
          <div className="flex items-center justify-between text-slate-400">
            <span>Environment</span>
            <span className="text-slate-200 font-medium">Razorpay Test</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Commit</span>
            <span className="text-slate-300">2dbc18b</span>
          </div>
          <div className="flex items-center justify-between text-slate-400 pt-0.5 border-t border-[#162030]">
            <span>Policy Authority</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <Lock className="w-2.5 h-2.5" /> Enforced
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
