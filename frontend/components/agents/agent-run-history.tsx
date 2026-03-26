import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { AgentRun } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function AgentRunHistory({ runs }: { runs: AgentRun[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent runs</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {runs.map((run) => (
          <div key={run.id} className="rounded-2xl border border-border bg-muted/20 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold">{run.agentName}</p>
                <p className="text-sm text-slate-500">{run.message}</p>
              </div>
              <p className="text-xs text-slate-500">{formatDate(run.createdAt)}</p>
            </div>
            <Progress value={run.progress} className="mt-3" />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
