import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { mockCampaigns } from "@/lib/mock-data";

export default function CampaignDetailPage({ params }: { params: { id: string } }) {
  const campaign = mockCampaigns.find((entry) => entry.id === params.id);

  if (!campaign) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
        { label: "Dashboard", href: "/" },
          { label: "Campaigns", href: "/campaigns" },
          { label: campaign.name }
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="font-display text-3xl font-semibold">{campaign.name}</h1>
                <p className="text-sm text-slate-500">{campaign.goal}</p>
              </div>
              <Badge tone={campaign.status === "active" ? "success" : "warning"}>{campaign.status}</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Tone</p>
                <p className="mt-1 font-semibold">{campaign.tone}</p>
              </div>
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Value prop</p>
                <p className="mt-1 font-semibold">{campaign.valueProp}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-3 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Sequence readiness</p>
            <p className="font-display text-2xl font-semibold">The agent will draft only when ICP fit meets the threshold.</p>
            <p className="text-sm text-slate-600">This is where future sequence steps, send windows, and attribution data will live.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
