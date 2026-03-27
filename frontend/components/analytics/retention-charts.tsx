"use client";

import { useQuery } from "@tanstack/react-query";
import { MetricCard } from "@/components/charts/metric-card";
import { LineChart } from "@/components/charts/line-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { fetchJson } from "@/lib/api";

type RetentionData = {
  at_risk_accounts: number;
  churn_risk: number;
  expansion_opportunities: number;
};

const fallbackHealthTrend = [
  { month: "Jan", value: 0 },
  { month: "Feb", value: 0 },
  { month: "Mar", value: 0 },
  { month: "Apr", value: 0 },
];

export function RetentionCharts() {
  const { data, isLoading } = useQuery<RetentionData>({
    queryKey: ["analytics", "retention"],
    queryFn: () => fetchJson<RetentionData>("/analytics/retention", {
      at_risk_accounts: 0,
      churn_risk: 0,
      expansion_opportunities: 0,
    }),
  });

  if (isLoading) {
    return <p className="p-4 text-sm text-slate-500">Loading…</p>;
  }

  const atRisk = data?.at_risk_accounts ?? 0;
  const churnRisk = data?.churn_risk ?? 0;
  const expansion = data?.expansion_opportunities ?? 0;

  const risk = [
    { name: "At risk", value: atRisk },
    { name: "Expansion", value: expansion },
    { name: "Healthy", value: Math.max(0, 100 - atRisk - expansion) },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="At-risk accounts" value={String(atRisk)} />
        <MetricCard label="Churn risk" value={`${(churnRisk * 100).toFixed(1)}%`} />
        <MetricCard label="Expansion opportunities" value={String(expansion)} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <LineChart title="Health score trend" data={fallbackHealthTrend} xKey="month" dataKey="value" />
        <DonutChart title="Health segments" data={risk} />
      </div>
    </div>
  );
}
