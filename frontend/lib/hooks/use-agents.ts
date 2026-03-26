import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import { mockAgentRuns, mockAgents } from "@/lib/mock-data";
import type { AgentRun, AgentSummary } from "@/lib/types";

export function useAgents() {
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => fetchJson<AgentSummary[]>("/agents", mockAgents)
  });

  const runs = useQuery({
    queryKey: ["agent-runs"],
    queryFn: () => fetchJson<AgentRun[]>("/jobs/runs", mockAgentRuns)
  });

  return { agents, runs };
}
