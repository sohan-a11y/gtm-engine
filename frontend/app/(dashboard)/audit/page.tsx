"use client";

import { useQuery } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { fetchJson } from "@/lib/api";
import type { Route } from "next";

type AuditEntry = {
  id: string;
  event_type: string;
  agent_name: string | null;
  message: string;
  created_at: string | null;
  metadata: Record<string, unknown>;
};

export default function AuditLogPage() {
  const { data: entries = [], isLoading } = useQuery<AuditEntry[]>({
    queryKey: ["audit-log"],
    queryFn: () => fetchJson<AuditEntry[]>("/notifications?limit=100", []),
  });

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" as Route }, { label: "Audit Log" }]} />
      <div className="space-y-1">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">History</p>
        <h1 className="font-display text-3xl font-semibold">Audit Log</h1>
      </div>
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-6 text-sm text-slate-500">Loading…</p>
          ) : entries.length === 0 ? (
            <p className="p-6 text-sm text-slate-500">No audit events yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Event</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Agent</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Details</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3">
                        <Badge tone="neutral" className="text-[10px]">
                          {entry.event_type.replace(/_/g, " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{entry.agent_name ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-700">{entry.message}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                        {entry.created_at
                          ? new Date(entry.created_at).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
