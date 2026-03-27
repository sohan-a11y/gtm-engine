"use client";

import { useQuery } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { fetchJson } from "@/lib/api";
import type { Route } from "next";

type Notification = {
  id: string;
  event_type: string;
  agent_name: string | null;
  message: string;
  created_at: string | null;
  metadata: Record<string, unknown>;
};

const EVENT_TONES: Record<string, "success" | "warning" | "danger" | "neutral" | "primary"> = {
  lead_scored: "success",
  outbound_draft_ready: "primary",
  sync_complete: "neutral",
  deal_risk_analyzed: "warning",
  agent_error: "danger",
};

export default function NotificationsPage() {
  const { data: notifications = [], isLoading } = useQuery<Notification[]>({
    queryKey: ["notifications"],
    queryFn: () => fetchJson<Notification[]>("/notifications", []),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" as Route }, { label: "Notifications" }]} />
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Activity</p>
        <h1 className="font-display text-3xl font-semibold">Notifications</h1>
      </div>
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-6 text-sm text-slate-500">Loading…</p>
          ) : notifications.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">
              No activity yet. Start by connecting your CRM or importing leads.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {notifications.map((n) => (
                <li key={n.id} className="flex items-start gap-4 p-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800">{n.message}</p>
                    {n.agent_name && (
                      <p className="text-xs text-slate-500 mt-0.5">via {n.agent_name}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge tone={EVENT_TONES[n.event_type] ?? "neutral"} className="text-[10px]">
                      {n.event_type.replace(/_/g, " ")}
                    </Badge>
                    {n.created_at && (
                      <span className="text-xs text-slate-400">
                        {new Date(n.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
