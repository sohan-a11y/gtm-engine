import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { LeadDetailCard } from "@/components/leads/lead-detail-card";
import { Card, CardContent } from "@/components/ui/card";
import { mockLeads } from "@/lib/mock-data";
import { notFound } from "next/navigation";

export default function LeadDetailPage({ params }: { params: { id: string } }) {
  const lead = mockLeads.find((entry) => entry.id === params.id);

  if (!lead) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
        { label: "Dashboard", href: "/" },
          { label: "Leads", href: "/leads" },
          { label: lead.name }
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <LeadDetailCard lead={lead} />
        <Card>
          <CardContent className="space-y-4 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Timeline</p>
            {[
              "Enriched from Apollo and Hunter",
              "ICP score crossed threshold",
              "Queued for review"
            ].map((entry) => (
              <div key={entry} className="rounded-2xl border border-border bg-white p-4 text-sm">
                {entry}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
