import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";

const pipelineData = [
  { stage: "Prospect", value: 18 },
  { stage: "Qualified", value: 11 },
  { stage: "Proposal", value: 8 },
  { stage: "Negotiation", value: 5 },
  { stage: "Won", value: 3 }
];

const trend = [
  { week: "W1", value: 8 },
  { week: "W2", value: 11 },
  { week: "W3", value: 14 },
  { week: "W4", value: 18 }
];

export function PipelineCharts() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Open opportunities" value="41" delta="+6 from last week" />
        <MetricCard label="Average stage velocity" value="11 days" delta="Down 2 days" />
        <MetricCard label="Forecast accuracy" value="92%" delta="Within tolerance" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Opportunities by stage" data={pipelineData} xKey="stage" dataKey="value" />
        <LineChart title="Qualified accounts by week" data={trend} xKey="week" dataKey="value" />
      </div>
    </div>
  );
}
