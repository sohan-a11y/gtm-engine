import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockCampaigns } from "@/lib/mock-data";
import type { Campaign } from "@/lib/types";

export function useCampaigns() {
  return useQuery({
    queryKey: ["campaigns"],
    queryFn: () => fetchJson<Campaign[]>("/campaigns", mockCampaigns)
  });
}
