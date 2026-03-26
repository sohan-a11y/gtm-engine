"use client";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { AgentCard } from "@/components/agents/agent-card";
import { AgentRunHistory } from "@/components/agents/agent-run-history";
import { useAgents } from "@/lib/hooks/use-agents";
import { useAgentEvents } from "@/lib/hooks/use-agent-events";

export default function AgentsPage() {
  const agents = useAgents();
  const events = useAgentEvents();

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Agents" }]} />
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Agent control center</p>
        <h1 className="font-display text-3xl font-semibold">Status, triggers, and run history</h1>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-4 md:grid-cols-2">
          {agents.agents.data?.map((agent) => <AgentCard key={agent.id} agent={agent} />)}
        </div>
        <div className="space-y-4">
          <AgentRunHistory runs={agents.runs.data ?? []} />
          <Card>
            <CardContent className="space-y-3 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Live SSE feed</p>
                <Badge tone={events.connected ? "success" : "warning"}>
                  {events.connected ? "Connected" : "Reconnecting"}
                </Badge>
              </div>
              <div className="space-y-2">
                {events.events.map((event, index) => (
                  <div key={`${event.type}-${index}`} className="rounded-2xl border border-border bg-white p-3 text-sm">
                    <p className="font-semibold">{event.agentName}</p>
                    <p className="text-slate-500">{event.message}</p>
                  </div>
                ))}
                {events.events.length === 0 ? (
                  <p className="text-sm text-slate-500">Waiting for agent activity...</p>
                ) : null}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
