import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import { backendCompanyToFrontend, unwrapItems } from "@/lib/transforms";

export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/companies?limit=200", []);
      return unwrapItems(raw as any).map((item: any) => backendCompanyToFrontend(item));
    },
  });
}
