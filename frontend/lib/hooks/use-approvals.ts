import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendApprovalToFrontend, unwrapItems } from "@/lib/transforms";
import type { ApprovalItem } from "@/lib/types";
import { useAppStore } from "@/lib/store";

export function useApprovals() {
  const selectedApprovalId = useAppStore((state) => state.selectedApprovalId);
  const selectApproval = useAppStore((state) => state.selectApproval);

  const query = useQuery({
    queryKey: ["approvals"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/approvals?limit=200", []);
      return unwrapItems(raw as any).map((item: any) => backendApprovalToFrontend(item));
    },
  });

  const currentItem = useMemo(
    () => query.data?.find((item) => item.id === selectedApprovalId) ?? query.data?.[0] ?? null,
    [query.data, selectedApprovalId]
  );

  return { ...query, currentItem, selectApproval };
}
