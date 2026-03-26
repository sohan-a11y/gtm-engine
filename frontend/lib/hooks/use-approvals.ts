import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockApprovals } from "@/lib/mock-data";
import type { ApprovalItem } from "@/lib/types";
import { useAppStore } from "@/lib/store";

export function useApprovals() {
  const selectedApprovalId = useAppStore((state) => state.selectedApprovalId);
  const selectApproval = useAppStore((state) => state.selectApproval);

  const query = useQuery({
    queryKey: ["approvals"],
    queryFn: () => fetchJson<ApprovalItem[]>("/approvals", mockApprovals)
  });

  const currentItem = useMemo(
    () => query.data?.find((item) => item.id === selectedApprovalId) ?? query.data?.[0] ?? null,
    [query.data, selectedApprovalId]
  );

  return {
    ...query,
    currentItem,
    selectApproval
  };
}
