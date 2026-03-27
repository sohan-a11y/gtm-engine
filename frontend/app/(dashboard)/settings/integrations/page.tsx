"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch, fetchJson, submitJson } from "@/lib/api";
import { unwrapItems } from "@/lib/transforms";

type Integration = {
  id: string;
  provider: string;
  status: string;
  last_synced_at: string | null;
};

const PROVIDER_META: Record<string, { label: string; description: string }> = {
  hubspot:    { label: "HubSpot",    description: "Sync contacts, companies, and deals" },
  salesforce: { label: "Salesforce", description: "Sync CRM records from Salesforce" },
  gmail:      { label: "Gmail",      description: "Send outbound sequences via Gmail" },
  outlook:    { label: "Outlook",    description: "Send outbound sequences via Microsoft 365" },
};

const ALL_PROVIDERS = Object.keys(PROVIDER_META);

export default function SettingsIntegrationsPage() {
  const qc = useQueryClient();
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const { data: integrations = [], isLoading } = useQuery<Integration[]>({
    queryKey: ["integrations"],
    queryFn: async () => {
      const raw = await fetchJson<unknown>("/integrations", []);
      return unwrapItems(raw as any) as Integration[];
    },
  });

  const disconnect = useMutation({
    mutationFn: async (id: string) => {
      await apiFetch(`/integrations/${id}`, { method: "DELETE" });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["integrations"] }),
  });

  async function handleSync(id: string) {
    setSyncingId(id);
    try {
      await submitJson(`/integrations/${id}/sync`, {});
      await qc.invalidateQueries({ queryKey: ["integrations"] });
    } finally {
      setSyncingId(null);
    }
  }

  function handleConnect(provider: string) {
    // OAuth providers: redirect to backend authorize endpoint
    window.location.href = `/api/integrations/${provider}/authorize`;
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/" },
          { label: "Settings", href: "/settings" },
          { label: "Integrations" },
        ]}
      />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Connections</p>
            <h1 className="font-display text-3xl font-semibold">
              Manage CRM, email, and enrichment providers
            </h1>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading integrations…</p>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {ALL_PROVIDERS.map((provider) => {
                const meta = PROVIDER_META[provider];
                const record = integrations.find((i) => i.provider === provider);
                const connected = record?.status === "connected";

                return (
                  <div key={provider} className="rounded-2xl border border-border bg-white p-4 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-semibold">{meta.label}</p>
                        <p className="text-xs text-slate-500">{meta.description}</p>
                      </div>
                      <Badge tone={connected ? "success" : "warning"}>
                        {connected ? "Connected" : "Disconnected"}
                      </Badge>
                    </div>

                    {record?.last_synced_at && (
                      <p className="text-xs text-slate-400">
                        Last synced: {new Date(record.last_synced_at).toLocaleString()}
                      </p>
                    )}

                    <div className="flex gap-2">
                      {connected && record ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={syncingId === record.id}
                            onClick={() => handleSync(record.id)}
                          >
                            {syncingId === record.id ? "Syncing…" : "Sync now"}
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => disconnect.mutate(record.id)}
                          >
                            Disconnect
                          </Button>
                        </>
                      ) : (
                        <Button size="sm" onClick={() => handleConnect(provider)}>
                          Connect
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
