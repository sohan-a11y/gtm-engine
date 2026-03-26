import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockLeads } from "@/lib/mock-data";
import type { Lead } from "@/lib/types";
import { useAppStore } from "@/lib/store";

export function useLeads() {
  const search = useAppStore((state) => state.leadSearch);

  return useQuery({
    queryKey: ["leads", search],
    queryFn: async () =>
      fetchJson<Lead[]>("/leads", mockLeads).then((rows) =>
        search.trim()
          ? rows.filter((lead) =>
              [lead.name, lead.company, lead.title, lead.email, lead.notes]
                .join(" ")
                .toLowerCase()
                .includes(search.toLowerCase())
            )
          : rows
      )
  });
}
