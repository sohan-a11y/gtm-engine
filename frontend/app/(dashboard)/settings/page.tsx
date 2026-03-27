"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchJson, submitJson } from "@/lib/api";

type OrgSettings = {
  org_name: string | null;
  timezone: string;
  notifications_enabled: boolean;
};

const TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
];

export default function SettingsPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<OrgSettings | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const { data: settings, isLoading } = useQuery<OrgSettings>({
    queryKey: ["settings"],
    queryFn: () => fetchJson<OrgSettings>("/settings", {
      org_name: null,
      timezone: "UTC",
      notifications_enabled: true,
    }),
  });

  const current = form ?? settings ?? { org_name: null, timezone: "UTC", notifications_enabled: true };

  function patch(updates: Partial<OrgSettings>) {
    setForm((prev) => ({ ...(prev ?? current), ...updates }));
  }

  const save = useMutation({
    mutationFn: async () => {
      const result = await submitJson("/settings", current, { method: "PATCH" });
      if (!result.ok) throw new Error("Save failed");
      return result.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
      setForm(null);
      setSaveError(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
    onError: (e: Error) => setSaveError(e.message),
  });

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings" }]} />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Workspace settings</p>
            <h1 className="font-display text-3xl font-semibold">General configuration</h1>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">Workspace name</label>
                  <Input
                    placeholder="Acme Corp"
                    value={current.org_name ?? ""}
                    onChange={(e) => patch({ org_name: e.target.value || null })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">Timezone</label>
                  <select
                    className="w-full rounded-xl border border-border bg-white px-3 py-2 text-sm"
                    value={current.timezone}
                    onChange={(e) => patch({ timezone: e.target.value })}
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-3 rounded-xl border border-border bg-slate-50 p-4">
                <input
                  id="notifs"
                  type="checkbox"
                  className="h-4 w-4 rounded"
                  checked={current.notifications_enabled}
                  onChange={(e) => patch({ notifications_enabled: e.target.checked })}
                />
                <label htmlFor="notifs" className="text-sm font-medium">
                  Enable in-app notifications
                  <span className="ml-1 font-normal text-slate-500">
                    (agent events, approvals, sync completions)
                  </span>
                </label>
              </div>

              {saveError && <p className="text-xs text-red-600">{saveError}</p>}
              {saved && <p className="text-xs text-emerald-600 font-medium">Settings saved.</p>}

              <Button onClick={() => save.mutate()} disabled={save.isPending}>
                {save.isPending ? "Saving…" : "Save changes"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
