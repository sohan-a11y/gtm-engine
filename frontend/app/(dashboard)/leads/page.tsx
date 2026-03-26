"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, FileUp } from "lucide-react";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { LeadImportDialog } from "@/components/leads/lead-import-dialog";
import { LeadTable } from "@/components/leads/lead-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useLeads } from "@/lib/hooks/use-leads";
import { useAppStore } from "@/lib/store";

export default function LeadsPage() {
  const leads = useLeads();
  const setLeadSearch = useAppStore((state) => state.setLeadSearch);
  const router = useRouter();

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Leads" }]} />
      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Lead workspace</p>
                <h1 className="font-display text-3xl font-semibold">Score, enrich, and prioritize</h1>
              </div>
              <Button variant="outline" onClick={() => setLeadSearch("")}>
                Reset search
              </Button>
            </div>
            <LeadTable data={leads.data ?? []} onRowClick={(lead) => router.push(`/leads/${lead.id}`)} />
          </CardContent>
        </Card>
        <div className="space-y-4">
          <LeadImportDialog />
          <Card>
            <CardContent className="space-y-4 p-5">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Next step</p>
              <p className="font-display text-2xl font-semibold">Turn high-fit leads into approved outbound</p>
              <Button asChild>
                <Link href="/approvals">
                  Review approvals
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <FileUp className="h-4 w-4" />
                CSV import, CRM sync, and enrichment hooks are ready in the scaffold.
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
