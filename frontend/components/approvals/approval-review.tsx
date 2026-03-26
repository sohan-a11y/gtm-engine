"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { ApprovalItem } from "@/lib/types";
import { IcpScoreBadge } from "@/components/leads/icp-score-badge";

export function ApprovalReview({
  item,
  onApprove,
  onReject,
  onSkip
}: {
  item: ApprovalItem | null;
  onApprove?: (variantId: string, body: string) => void;
  onReject?: (reason: string) => void;
  onSkip?: () => void;
}) {
  const [variantId, setVariantId] = useState(item?.variants[0]?.id ?? "");
  const [reason, setReason] = useState("");

  useEffect(() => {
    setVariantId(item?.variants[0]?.id ?? "");
    setReason("");
  }, [item]);

  const variant = useMemo(
    () => item?.variants.find((entry) => entry.id === variantId) ?? item?.variants[0] ?? null,
    [item, variantId]
  );

  if (!item) {
    return (
      <Card className="h-full">
        <CardContent className="flex h-full items-center justify-center p-8 text-slate-500">
          Pick an approval on the left to inspect the lead context and draft variants.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>{item.lead.name}</CardTitle>
            <p className="mt-1 text-sm text-slate-600">
              {item.lead.title} at {item.lead.company}
            </p>
          </div>
          <IcpScoreBadge score={item.lead.icpScore} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge tone="primary">{item.campaign}</Badge>
          <Badge tone="neutral">{item.lead.email}</Badge>
          <Badge tone="neutral">{item.lead.city}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-3">
          {item.variants.map((entry) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => setVariantId(entry.id)}
              className={`rounded-2xl border p-3 text-left transition ${
                variant?.id === entry.id ? "border-primary bg-primary/5 shadow-soft" : "border-border bg-white hover:bg-muted/40"
              }`}
            >
              <p className="text-sm font-semibold">{entry.subject}</p>
              <p className="mt-1 text-xs text-slate-500">{entry.hookType}</p>
              <p className="mt-2 text-xs font-semibold text-slate-600">{Math.round(entry.confidence * 100)}% confidence</p>
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-border bg-muted/20 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Selected draft</p>
          <p className="mt-2 font-display text-lg font-semibold">{variant?.subject}</p>
          <p className="mt-3 text-sm leading-7 text-slate-700">{variant?.body}</p>
        </div>

        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Rejection reason</p>
          <Textarea
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Use this if you need to reject or send back for revision."
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => onApprove?.(variant?.id ?? "", variant?.body ?? "")}>Approve</Button>
          <Button
            variant="outline"
            onClick={() => onApprove?.(variant?.id ?? "", `${variant?.body ?? ""}\n\n[edited by reviewer]`)}
          >
            Edit + approve
          </Button>
          <Button variant="outline" onClick={() => onReject?.(reason)}>
            Reject
          </Button>
          <Button variant="ghost" onClick={() => onSkip?.()}>
            Skip
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
