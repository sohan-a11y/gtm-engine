"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { DataTable, type Column } from "@/components/common/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCampaigns } from "@/lib/hooks/use-campaigns";
import type { Campaign } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const columns: Column<Campaign>[] = [
  { key: "name", header: "Campaign", accessor: (campaign) => campaign.name, sortable: true, sortValue: (campaign) => campaign.name },
  { key: "goal", header: "Goal", accessor: (campaign) => campaign.goal },
  { key: "status", header: "Status", accessor: (campaign) => <Badge tone={campaign.status === "active" ? "success" : "warning"}>{campaign.status}</Badge> },
  { key: "sent", header: "Sent", accessor: (campaign) => campaign.sent, sortable: true, sortValue: (campaign) => campaign.sent },
  { key: "created", header: "Created", accessor: (campaign) => formatDate(campaign.createdAt) }
];

export default function CampaignsPage() {
  const campaigns = useCampaigns();
  const router = useRouter();

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Campaigns" }]} />
      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Campaign studio</p>
                <h1 className="font-display text-3xl font-semibold">Coordinate outbound sequences by segment</h1>
              </div>
              <Button asChild>
                <Link href="/campaigns/new">
                  New campaign
                  <Plus className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            <DataTable
              data={campaigns.data ?? []}
              columns={columns}
              searchable={(campaign) => [campaign.name, campaign.goal, campaign.valueProp].join(" ")}
              onRowClick={(campaign) => router.push(`/campaigns/${campaign.id}`)}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-3 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Guidance</p>
            <p className="font-display text-2xl font-semibold">Each campaign is scored, reviewed, and approved before external send.</p>
            <p className="text-sm text-slate-600">
              The scaffold keeps campaign configuration, ICP thresholding, and approval handoff in one place.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
