"use client";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { EmptyState } from "@/components/common/empty-state";
import { ApprovalList } from "@/components/approvals/approval-list";
import { ApprovalReview } from "@/components/approvals/approval-review";
import { ApprovalStatsBar } from "@/components/approvals/approval-stats-bar";
import { useApprovals } from "@/lib/hooks/use-approvals";

export default function ApprovalsPage() {
  const approvals = useApprovals();

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Approvals" }]} />
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Human-in-the-loop</p>
        <h1 className="font-display text-3xl font-semibold">Approve, edit, reject, or skip drafts</h1>
      </div>
      <ApprovalStatsBar pending={approvals.data?.length ?? 0} approved={0} rejected={0} />
      {approvals.data?.length ? (
        <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <ApprovalList
            items={approvals.data}
            selectedId={approvals.currentItem?.id ?? null}
            onSelect={approvals.selectApproval}
          />
          <ApprovalReview item={approvals.currentItem} />
        </div>
      ) : (
        <EmptyState
          title="No approvals queued"
          description="Once the outbound agent drafts a review-ready sequence, it will appear here for human approval."
        />
      )}
    </div>
  );
}
