"use client";

import { useQuery } from "@tanstack/react-query";
import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";
import { fetchJson } from "@/lib/api";

type PipelineData = {
  open_deals: number;
  won_deals: number;
  lost_deals: number;
  conversion_rate: number;
  series?: Array<{ timestamp: string; value: number; label?: string | null }>;
};

const fallbackPipelineData = [
  { stage: "Prospect", value: 0 },
  { stage: "Qualified", value: 0 },
  { stage: "Proposal", value: 0 },
  { stage: "Negotiation", value: 0 },
  { stage: "Won", value: 0 },
];

const fallbackTrend = [
  { week: "W1", value: 0 },
  { week: "W2", value: 0 },
  { week: "W3", value: 0 },
  { week: "W4", value: 0 },
];

export function PipelineCharts() {
  const { data, isLoading } = useQuery<PipelineData>({
    queryKey: ["analytics", "pipeline"],
    queryFn: () => fetchJson<PipelineData>("/analytics/pipeline", {
      open_deals: 0,
      won_deals: 0,
      lost_deals: 0,
      conversion_rate: 0,
    }),
  });

  if (isLoading) {
    return <p className="p-4 text-sm text-slate-500">Loading…</p>;
  }

  const openDeals = data?.open_deals ?? 0;
  const wonDeals = data?.won_deals ?? 0;
  const conversionRate = data?.conversion_rate ?? 0;

  const pipelineData = wonDeals > 0
    ? [{ stage: "Won", value: wonDeals }, { stage: "Lost", value: data?.lost_deals ?? 0 }, { stage: "Open", value: openDeals }]
    : fallbackPipelineData;

  const trend = data?.series && data.series.length > 0
    ? data.series.map((p, i) => ({ week: `W${i + 1}`, value: p.value }))
    : fallbackTrend;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Open opportunities" value={String(openDeals)} delta="" />
        <MetricCard label="Won deals" value={String(wonDeals)} delta="" />
        <MetricCard label="Conversion rate" value={`${(conversionRate * 100).toFixed(1)}%`} delta="" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Opportunities by stage" data={pipelineData} xKey="stage" dataKey="value" />
        <LineChart title="Pipeline trend" data={trend} xKey="week" dataKey="value" />
      </div>
    </div>
  );
}
