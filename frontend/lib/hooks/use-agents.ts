import { useQuery } from "@tanstack/react-query";
import { fetchJson } from "@/lib/api";
import type { AgentRun, AgentSummary } from "@/lib/types";

export function useAgents() {
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => fetchJson<AgentSummary[]>("/agents", []),
  });

  const runs = useQuery({
    queryKey: ["agent-runs"],
    queryFn: () => fetchJson<AgentRun[]>("/jobs/runs", []),
  });

  return { agents, runs };
}
