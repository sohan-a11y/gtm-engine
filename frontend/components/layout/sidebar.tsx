"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  BriefcaseBusiness,
  LayoutDashboard,
  Lightbulb,
  Settings2,
  ShieldCheck,
  Target,
  Users2
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation: Array<{ href: Route; label: string; icon: typeof LayoutDashboard }> = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users2 },
  { href: "/companies", label: "Companies", icon: BriefcaseBusiness },
  { href: "/campaigns", label: "Campaigns", icon: Target },
  { href: "/pipeline", label: "Pipeline", icon: Activity },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/agents", label: "Agents", icon: Lightbulb },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings2 }
];

export function Sidebar({ collapsed = false }: { collapsed?: boolean }) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "glass-panel panel-ring sticky top-4 hidden h-[calc(100vh-2rem)] shrink-0 flex-col overflow-hidden rounded-3xl border border-border/80 p-4 shadow-soft lg:flex",
        collapsed ? "w-[88px]" : "w-[272px]"
      )}
    >
      <div className="flex items-center justify-between gap-3 px-2 pb-4">
        <div>
          <p className="font-display text-lg font-semibold tracking-tight">Artifex</p>
          {!collapsed ? <p className="text-xs text-slate-500">AI GTM Engine</p> : null}
        </div>
        <Badge tone="primary" className="border-0">
          Live
        </Badge>
      </div>

      <nav className="flex-1 space-y-1">
        {navigation.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition",
                active ? "bg-primary text-primary-foreground shadow-soft" : "text-slate-600 hover:bg-muted/80 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed ? <span>{item.label}</span> : null}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 rounded-2xl border border-border bg-white p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Agent health</p>
        <div className="mt-3 flex items-center gap-3">
          <span className="h-2.5 w-2.5 rounded-full bg-success shadow-[0_0_0_6px_rgba(34,197,94,0.12)]" />
          {!collapsed ? (
            <div>
              <p className="text-sm font-semibold">4 agents ready</p>
              <p className="text-xs text-slate-500">3 active workflows, 1 idle</p>
            </div>
          ) : null}
        </div>
        {!collapsed ? (
          <Button variant="outline" size="sm" className="mt-4 w-full">
            Open review queue
          </Button>
        ) : null}
      </div>
    </aside>
  );
}
