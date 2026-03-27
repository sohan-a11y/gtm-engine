import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendCampaignToFrontend, unwrapItems } from "@/lib/transforms";
import type { Campaign } from "@/lib/types";

export function useCampaigns() {
  return useQuery({
    queryKey: ["campaigns"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/campaigns?limit=200", []);
      return unwrapItems(raw as any).map((item: any) => backendCampaignToFrontend(item));
    },
  });
}
