import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatDate, formatPercent } from "@/lib/utils";
import type { Lead } from "@/lib/types";
import { IcpScoreBadge } from "@/components/leads/icp-score-badge";

export function LeadDetailCard({ lead }: { lead: Lead }) {
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>{lead.name}</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              {lead.title} at {lead.company}
            </p>
          </div>
          <IcpScoreBadge score={lead.icpScore} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone="primary">{lead.status}</Badge>
          <Badge tone="neutral">{lead.city}</Badge>
          <Badge tone="neutral">{lead.email}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-border bg-muted/30 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Risk</p>
            <div className="mt-2 flex items-end justify-between gap-3">
              <p className="font-display text-3xl font-semibold">{formatPercent(lead.emailRisk)}</p>
              <p className="text-sm text-slate-500">Deliverability confidence</p>
            </div>
            <Progress value={lead.emailRisk * 100} className="mt-4" />
          </div>
          <div className="rounded-2xl border border-border bg-muted/30 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Enrichment</p>
            <p className="mt-2 font-semibold">{lead.enrichment.source}</p>
            <p className="text-sm text-slate-500">{lead.enrichment.employees} employees</p>
            <p className="text-sm text-slate-500">{lead.enrichment.revenue}</p>
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">Context notes</h4>
          <p className="rounded-2xl border border-border bg-white p-4 text-sm leading-6 text-slate-700">
            {lead.notes}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {lead.enrichment.technologies.map((technology) => (
            <Badge key={technology} tone="neutral">
              {technology}
            </Badge>
          ))}
        </div>

        <p className="text-xs text-slate-500">Last touched {formatDate(lead.lastTouchedAt)}</p>
      </CardContent>
    </Card>
  );
}
