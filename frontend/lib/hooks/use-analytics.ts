import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendAnalyticsToFrontend } from "@/lib/transforms";
import type { AnalyticsSnapshot } from "@/lib/types";

const EMPTY: AnalyticsSnapshot = {
  leadsScored: 0,
  emailsGenerated: 0,
  emailsApproved: 0,
  activeCampaigns: 0,
  pipelineValue: 0,
  churnAtRisk: 0,
};

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/analytics/summary", null);
      if (!raw) return EMPTY;
      return backendAnalyticsToFrontend(raw as any);
    },
    refetchInterval: 30_000,
  });
}
