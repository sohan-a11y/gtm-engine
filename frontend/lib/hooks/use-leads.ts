import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendLeadToFrontend, unwrapItems } from "@/lib/transforms";
import type { Lead } from "@/lib/types";
import { useAppStore } from "@/lib/store";

export function useLeads() {
  const search = useAppStore((state) => state.leadSearch);

  return useQuery({
    queryKey: ["leads", search],
    queryFn: async () => {
      const raw = await fetchJson<{ items: Lead[] } | Lead[]>(
        search.trim() ? `/leads?search=${encodeURIComponent(search)}&limit=200` : "/leads?limit=200",
        []
      );
      return unwrapItems(raw as { items: unknown[]; total: number; page: number; page_size: number }).map(
        (item) => backendLeadToFrontend(item as Parameters<typeof backendLeadToFrontend>[0])
      );
    },
  });
}
