import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockAnalytics } from "@/lib/mock-data";
import type { AnalyticsSnapshot } from "@/lib/types";

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: () => fetchJson<AnalyticsSnapshot>("/analytics/summary", mockAnalytics),
    refetchInterval: 30_000
  });
}
