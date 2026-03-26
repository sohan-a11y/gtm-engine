import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Tabs } from "@/components/ui/tabs";
import { PipelineCharts } from "@/components/analytics/pipeline-charts";
import { OutboundCharts } from "@/components/analytics/outbound-charts";
import { RetentionCharts } from "@/components/analytics/retention-charts";
import { AiUsageCharts } from "@/components/analytics/ai-usage-charts";

export default function AnalyticsPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Analytics" }]} />
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Analytics</p>
        <h1 className="font-display text-3xl font-semibold">Four views for pipeline, outbound, retention, and AI usage</h1>
      </div>
      <Tabs
        defaultValue="pipeline"
        items={[
          { value: "pipeline", label: "Pipeline", content: <PipelineCharts /> },
          { value: "outbound", label: "Outbound", content: <OutboundCharts /> },
          { value: "retention", label: "Retention", content: <RetentionCharts /> },
          { value: "ai", label: "AI Usage", content: <AiUsageCharts /> }
        ]}
      />
    </div>
  );
}
