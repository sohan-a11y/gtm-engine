"use client";

import { useQuery } from "@tanstack/react-query";
import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { fetchJson } from "@/lib/api";

type OutboundData = {
  drafts_created: number;
  approved: number;
  sent: number;
  reply_rate: number;
};

const fallbackSends = [
  { week: "W1", value: 0 },
  { week: "W2", value: 0 },
  { week: "W3", value: 0 },
  { week: "W4", value: 0 },
];

const fallbackHooks = [
  { name: "Pain point", value: 0 },
  { name: "Efficiency", value: 0 },
  { name: "Social proof", value: 0 },
  { name: "Reframe", value: 0 },
];

export function OutboundCharts() {
  const { data, isLoading } = useQuery<OutboundData>({
    queryKey: ["analytics", "outbound"],
    queryFn: () => fetchJson<OutboundData>("/analytics/outbound", {
      drafts_created: 0,
      approved: 0,
      sent: 0,
      reply_rate: 0,
    }),
  });

  if (isLoading) {
    return <p className="p-4 text-sm text-slate-500">Loading…</p>;
  }

  const sent = data?.sent ?? 0;
  const replyRate = data?.reply_rate ?? 0;
  const approved = data?.approved ?? 0;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Emails sent" value={String(sent)} />
        <MetricCard label="Reply rate" value={`${(replyRate * 100).toFixed(1)}%`} />
        <MetricCard label="Approved drafts" value={String(approved)} delta="Human-in-the-loop active" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Outbound volume" data={fallbackSends} xKey="week" dataKey="value" />
        <DonutChart title="Hook mix" data={fallbackHooks} />
      </div>
    </div>
  );
}
