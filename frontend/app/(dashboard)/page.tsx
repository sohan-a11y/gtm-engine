"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { AgentCard } from "@/components/agents/agent-card";
import { AgentRunHistory } from "@/components/agents/agent-run-history";
import { MetricCard } from "@/components/charts/metric-card";
import { LoadingSkeleton } from "@/components/common/loading-skeleton";
import { ApprovalList } from "@/components/approvals/approval-list";
import { ApprovalReview } from "@/components/approvals/approval-review";
import { IcpScoreBadge } from "@/components/leads/icp-score-badge";
import { LeadDetailCard } from "@/components/leads/lead-detail-card";
import { useAgents } from "@/lib/hooks/use-agents";
import { useAnalytics } from "@/lib/hooks/use-analytics";
import { useApprovals } from "@/lib/hooks/use-approvals";
import { useLeads } from "@/lib/hooks/use-leads";
import { formatCurrency, formatNumber } from "@/lib/utils";

export default function DashboardPage() {
  const analytics = useAnalytics();
  const agents = useAgents();
  const approvals = useApprovals();
  const leads = useLeads();

  const currentLead = leads.data?.[0] ?? null;
  const loading =
    analytics.isLoading || agents.agents.isLoading || agents.runs.isLoading || approvals.isLoading || leads.isLoading;

  if (loading) {
    return <LoadingSkeleton rows={6} />;
  }

  return (
    <div className="space-y-4">
      <section className="grid gap-4 xl:grid-cols-4">
        <MetricCard label="Leads scored" value={formatNumber(analytics.data?.leadsScored ?? 0)} delta="+14% from last week" />
        <MetricCard label="Emails generated" value={formatNumber(analytics.data?.emailsGenerated ?? 0)} delta="82 approved drafts" />
        <MetricCard label="Pipeline value" value={formatCurrency(analytics.data?.pipelineValue ?? 0)} delta="3 active opportunities" />
        <MetricCard label="At-risk accounts" value={formatNumber(analytics.data?.churnAtRisk ?? 0)} delta="Retention watchlist updated" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Live queue</p>
                <h2 className="font-display text-2xl font-semibold">Approvals waiting for review</h2>
              </div>
              <Badge tone="warning">{approvals.data?.length ?? 0} pending</Badge>
            </div>
            <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <ApprovalList
                items={approvals.data ?? []}
                selectedId={approvals.currentItem?.id ?? null}
                onSelect={approvals.selectApproval}
              />
              <ApprovalReview item={approvals.currentItem} />
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Signal</p>
                  <h2 className="font-display text-2xl font-semibold">Current ICP fit</h2>
                </div>
                {currentLead ? <IcpScoreBadge score={currentLead.icpScore} /> : null}
              </div>
              {currentLead ? <LeadDetailCard lead={currentLead} /> : null}
            </CardContent>
          </Card>

          <AgentRunHistory runs={agents.runs.data ?? []} />
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">Agents</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {agents.agents.data?.map((agent) => <AgentCard key={agent.id} agent={agent} />)}
          </div>
        </div>
        <Card>
          <CardContent className="space-y-3 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Recent activity</p>
            <div className="space-y-3">
              {[
                "Northstar Analytics moved into approval.",
                "ICP retrained with 5 verified customer examples.",
                "Outbound Agent generated 3 hook variants."
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-border bg-white p-4 text-sm text-slate-700">
                  {item}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
