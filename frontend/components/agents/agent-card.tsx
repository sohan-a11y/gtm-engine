import { PlayCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AgentStatusBadge } from "@/components/agents/agent-status-badge";
import type { AgentSummary } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/utils";

export function AgentCard({ agent, onTrigger }: { agent: AgentSummary; onTrigger?: () => void }) {
  return (
    <Card className="h-full">
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle>{agent.name}</CardTitle>
            <p className="mt-1 text-sm text-slate-600">{agent.description}</p>
          </div>
          <AgentStatusBadge status={agent.status} />
        </div>
        <Badge tone="neutral" className="w-fit">
          {agent.triggerLabel}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-500">Success rate</span>
            <span className="font-semibold">{formatNumber(agent.successRate * 100)}%</span>
          </div>
          <Progress value={agent.successRate * 100} className="mt-2" />
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl border border-border bg-muted/20 p-3">
            <p className="text-slate-500">Latency</p>
            <p className="font-semibold">{formatNumber(agent.avgLatencyMs)} ms</p>
          </div>
          <div className="rounded-2xl border border-border bg-muted/20 p-3">
            <p className="text-slate-500">Last run</p>
            <p className="font-semibold">{formatDate(agent.lastRunAt)}</p>
          </div>
        </div>
        <Button variant="outline" className="w-full" onClick={onTrigger}>
          <PlayCircle className="h-4 w-4" />
          Trigger run
        </Button>
      </CardContent>
    </Card>
  );
}
