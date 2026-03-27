"use client";

import { useQuery } from "@tanstack/react-query";
import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";
import { fetchJson } from "@/lib/api";

type AnalyticsOverview = {
  ai_usage: Record<string, number>;
  pipeline?: unknown;
  outbound?: unknown;
  retention?: unknown;
};

const fallbackUsage = [
  { day: "Mon", value: 0 },
  { day: "Tue", value: 0 },
  { day: "Wed", value: 0 },
  { day: "Thu", value: 0 },
  { day: "Fri", value: 0 },
];

const fallbackLatency = [
  { day: "Mon", value: 0 },
  { day: "Tue", value: 0 },
  { day: "Wed", value: 0 },
  { day: "Thu", value: 0 },
  { day: "Fri", value: 0 },
];

export function AiUsageCharts() {
  const { data, isLoading } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", "usage"],
    queryFn: () => fetchJson<AnalyticsOverview>("/analytics/usage", { ai_usage: {} }),
  });

  if (isLoading) {
    return <p className="p-4 text-sm text-slate-500">Loading…</p>;
  }

  const aiUsage = data?.ai_usage ?? {};
  const leadsScored = aiUsage.leads_scored ?? 0;
  const llmCalls = aiUsage.llm_calls ?? 0;
  const tokensConsumed = aiUsage.tokens_consumed ?? 0;
  const avgLatency = aiUsage.avg_latency_ms ?? 0;

  const tokensLabel = tokensConsumed >= 1_000_000
    ? `${(tokensConsumed / 1_000_000).toFixed(1)}M`
    : tokensConsumed >= 1_000
    ? `${(tokensConsumed / 1_000).toFixed(0)}K`
    : String(tokensConsumed);

  const latencyLabel = avgLatency > 0 ? `${(avgLatency / 1000).toFixed(1)}s` : "—";

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="LLM calls" value={llmCalls > 0 ? String(llmCalls) : String(leadsScored)} />
        <MetricCard label="Tokens consumed" value={tokensLabel || "—"} />
        <MetricCard label="Average latency" value={latencyLabel} delta="Under target" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Daily LLM calls" data={fallbackUsage} xKey="day" dataKey="value" />
        <LineChart title="Latency trend" data={fallbackLatency} xKey="day" dataKey="value" />
      </div>
    </div>
  );
}
