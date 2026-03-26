import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockCompanies } from "@/lib/mock-data";
import type { Company } from "@/lib/types";

export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: () => fetchJson<Company[]>("/companies", mockCompanies)
  });
}
