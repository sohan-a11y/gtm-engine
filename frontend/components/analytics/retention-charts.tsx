import { MetricCard } from "@/components/charts/metric-card";
import { LineChart } from "@/components/charts/line-chart";
import { DonutChart } from "@/components/charts/donut-chart";

const healthTrend = [
  { month: "Jan", value: 72 },
  { month: "Feb", value: 76 },
  { month: "Mar", value: 81 },
  { month: "Apr", value: 84 }
];

const risk = [
  { name: "Healthy", value: 67 },
  { name: "Watch", value: 19 },
  { name: "At risk", value: 14 }
];

export function RetentionCharts() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Accounts monitored" value="84" delta="+12 this month" />
        <MetricCard label="Churn risk" value="14" delta="-4 from last cycle" />
        <MetricCard label="Health score" value="81" delta="Stable trending up" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <LineChart title="Health score trend" data={healthTrend} xKey="month" dataKey="value" />
        <DonutChart title="Health segments" data={risk} />
      </div>
    </div>
  );
}
