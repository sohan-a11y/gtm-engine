"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { submitJson } from "@/lib/api";
import { useDeals } from "@/lib/hooks/use-deals";
import type { Deal } from "@/lib/types";

const STAGES: { key: string; label: string }[] = [
  { key: "prospecting", label: "Prospect" },
  { key: "qualified",   label: "Qualified" },
  { key: "proposal",    label: "Proposal" },
  { key: "negotiation", label: "Negotiation" },
  { key: "closed_won",  label: "Won" },
];

function riskTone(score: number | null): "success" | "warning" | "danger" | "neutral" {
  if (score == null) return "neutral";
  if (score < 0.4)   return "success";
  if (score < 0.75)  return "warning";
  return "danger";
}

function fmt(amount: number) {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000)     return `$${(amount / 1_000).toFixed(0)}k`;
  return `$${amount.toFixed(0)}`;
}

export default function PipelinePage() {
  const { data: deals = [], isLoading } = useDeals();
  const qc = useQueryClient();

  const analyzeRisk = useMutation({
    mutationFn: async (dealId: string) => {
      await submitJson(`/deals/${dealId}/risk`, {});
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });

  const byStage = (stageKey: string): Deal[] =>
    deals.filter((d) => (d.stage ?? "prospecting") === stageKey);

  const totalOpen = deals
    .filter((d) => !["closed_won", "closed_lost"].includes(d.stage))
    .reduce((s, d) => s + d.amount, 0);

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Pipeline" }]} />
      <div className="flex items-end justify-between">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Deal pipeline</p>
          <h1 className="font-display text-3xl font-semibold">Kanban with risk indicators</h1>
        </div>
        {totalOpen > 0 && (
          <p className="text-sm text-slate-500">
            Open pipeline: <span className="font-semibold text-slate-800">{fmt(totalOpen)}</span>
          </p>
        )}
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Loading deals…</p>
      ) : deals.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-slate-500">
            No deals yet. Connect your CRM or create your first deal.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-5">
          {STAGES.map(({ key, label }) => {
            const items = byStage(key);
            return (
              <Card key={key}>
                <CardContent className="space-y-3 p-4">
                  <div className="flex items-center justify-between">
                    <h2 className="font-semibold">{label}</h2>
                    <Badge tone="neutral">{items.length}</Badge>
                  </div>
                  <div className="space-y-3">
                    {items.length === 0 ? (
                      <p className="text-xs text-slate-400 py-2 text-center">Empty</p>
                    ) : (
                      items.map((deal) => (
                        <div
                          key={deal.id}
                          className="rounded-2xl border border-border bg-white p-3 text-sm space-y-2"
                        >
                          <p className="font-semibold leading-tight">{deal.name}</p>
                          {deal.amount > 0 && (
                            <p className="text-xs text-slate-500">{fmt(deal.amount)}</p>
                          )}
                          <div className="flex items-center justify-between gap-2">
                            {deal.riskScore != null ? (
                              <Badge tone={riskTone(deal.riskScore)} className="text-[10px]">
                                Risk {Math.round(deal.riskScore * 100)}%
                              </Badge>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-5 px-1 text-[10px]"
                                disabled={analyzeRisk.isPending}
                                onClick={() => analyzeRisk.mutate(deal.id)}
                              >
                                Score risk
                              </Button>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
