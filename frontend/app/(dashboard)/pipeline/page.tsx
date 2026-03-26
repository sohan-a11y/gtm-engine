import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const stages = [
  { name: "Prospect", items: ["Northstar Analytics", "Vertex Labs"] },
  { name: "Qualified", items: ["Vector Forge"] },
  { name: "Proposal", items: ["Atlas Systems"] },
  { name: "Negotiation", items: ["Signal Harbor"] }
];

export default function PipelinePage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Pipeline" }]} />
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Deal pipeline</p>
        <h1 className="font-display text-3xl font-semibold">Kanban with risk indicators</h1>
      </div>
      <div className="grid gap-4 xl:grid-cols-4">
        {stages.map((stage) => (
          <Card key={stage.name}>
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">{stage.name}</h2>
                <Badge tone="neutral">{stage.items.length}</Badge>
              </div>
              <div className="space-y-3">
                {stage.items.map((item) => (
                  <div key={item} className="rounded-2xl border border-border bg-white p-4 text-sm">
                    <p className="font-semibold">{item}</p>
                    <p className="mt-1 text-xs text-slate-500">Risk under review</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
