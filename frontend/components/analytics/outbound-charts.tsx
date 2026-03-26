import { MetricCard } from "@/components/charts/metric-card";
import { BarChart } from "@/components/charts/bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";

const sends = [
  { week: "W1", value: 44 },
  { week: "W2", value: 61 },
  { week: "W3", value: 78 },
  { week: "W4", value: 92 }
];

const hooks = [
  { name: "Pain point", value: 41 },
  { name: "Efficiency", value: 28 },
  { name: "Social proof", value: 19 },
  { name: "Reframe", value: 12 }
];

export function OutboundCharts() {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Emails sent" value="316" delta="+18% reply-ready volume" />
        <MetricCard label="Reply rate" value="16%" delta="Target exceeded" />
        <MetricCard label="Approved drafts" value="82" delta="Human-in-the-loop active" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <BarChart title="Outbound volume" data={sends} xKey="week" dataKey="value" />
        <DonutChart title="Hook mix" data={hooks} />
      </div>
    </div>
  );
}
