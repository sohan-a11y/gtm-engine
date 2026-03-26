import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";

const usage = [
  { day: "Mon", value: 128 },
  { day: "Tue", value: 161 },
  { day: "Wed", value: 190 },
  { day: "Thu", value: 174 },
  { day: "Fri", value: 208 }
];

const latency = [
  { day: "Mon", value: 1.4 },
  { day: "Tue", value: 1.3 },
  { day: "Wed", value: 1.5 },
  { day: "Thu", value: 1.2 },
  { day: "Fri", value: 1.1 }
];

export function AiUsageCharts() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="LLM calls" value="861" delta="+9% vs previous week" />
        <MetricCard label="Tokens consumed" value="3.2M" delta="Cost optimized" />
        <MetricCard label="Average latency" value="1.3s" delta="Under target" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Daily LLM calls" data={usage} xKey="day" dataKey="value" />
        <LineChart title="Latency trend" data={latency} xKey="day" dataKey="value" />
      </div>
    </div>
  );
}
