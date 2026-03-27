import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendDealToFrontend, unwrapItems } from "@/lib/transforms";
import type { Deal } from "@/lib/types";

export function useDeals() {
  return useQuery<Deal[]>({
    queryKey: ["deals"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/deals?limit=200", []);
      return unwrapItems(raw as any).map((item: any) => backendDealToFrontend(item));
    },
  });
}
