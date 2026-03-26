import { Badge } from "@/components/ui/badge";
import type { AgentStatus } from "@/lib/types";

const tones: Record<AgentStatus, "neutral" | "success" | "warning" | "danger" | "primary"> = {
  idle: "neutral",
  running: "primary",
  healthy: "success",
  paused: "warning",
  error: "danger"
};

export function AgentStatusBadge({ status }: { status: AgentStatus }) {
  return <Badge tone={tones[status]}>{status}</Badge>;
}
