"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchJson, submitJson } from "@/lib/api";

type LLMConfig = {
  provider: string;
  model: string;
  api_key: string | null;
  temperature: number;
};

const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
  anthropic: ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
  ollama: ["llama3", "mistral", "gemma2", "phi3"],
  groq: ["llama-3.1-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
  azure: ["gpt-4", "gpt-4o", "gpt-35-turbo"],
};

const PROVIDERS = Object.keys(PROVIDER_MODELS);
const NEEDS_BASE_URL = ["ollama", "azure"];

export default function SettingsLLMPage() {
  const qc = useQueryClient();
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const { data: config, isLoading } = useQuery<LLMConfig>({
    queryKey: ["settings-llm"],
    queryFn: () => fetchJson<LLMConfig>("/settings/llm-config", {
      provider: "openai",
      model: "gpt-4.1-mini",
      api_key: null,
      temperature: 0.2,
    }),
  });

  const [form, setForm] = useState<LLMConfig | null>(null);
  const current = form ?? config ?? { provider: "openai", model: "gpt-4.1-mini", api_key: null, temperature: 0.2 };

  function patch(updates: Partial<LLMConfig>) {
    setForm((prev) => ({ ...(prev ?? current), ...updates }));
  }

  const save = useMutation({
    mutationFn: async () => {
      const result = await submitJson("/settings/llm-config", current, { method: "PATCH" });
      if (!result.ok) throw new Error("Save failed");
      return result.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings-llm"] });
      setForm(null);
      setSaveError(null);
    },
    onError: (e: Error) => setSaveError(e.message),
  });

  async function testConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await submitJson("/agents/test-llm", current);
      setTestResult(result.ok ? "Connection successful" : "Connection failed");
    } catch {
      setTestResult("Connection failed");
    } finally {
      setTesting(false);
    }
  }

  const models = PROVIDER_MODELS[current.provider] ?? [];

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/" },
          { label: "Settings", href: "/settings" },
          { label: "LLM" },
        ]}
      />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">LLM configuration</p>
            <h1 className="font-display text-3xl font-semibold">
              Select provider, model, and fallback policy
            </h1>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">Provider</label>
                  <select
                    className="w-full rounded-xl border border-border bg-white px-3 py-2 text-sm"
                    value={current.provider}
                    onChange={(e) => {
                      const p = e.target.value;
                      const firstModel = PROVIDER_MODELS[p]?.[0] ?? "";
                      patch({ provider: p, model: firstModel });
                    }}
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">Model</label>
                  <select
                    className="w-full rounded-xl border border-border bg-white px-3 py-2 text-sm"
                    value={current.model}
                    onChange={(e) => patch({ model: e.target.value })}
                  >
                    {models.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">API Key</label>
                  <Input
                    type="password"
                    placeholder="sk-…"
                    value={current.api_key ?? ""}
                    onChange={(e) => patch({ api_key: e.target.value || null })}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-600">Temperature</label>
                  <Input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={current.temperature}
                    onChange={(e) => patch({ temperature: parseFloat(e.target.value) || 0.2 })}
                  />
                </div>

                {NEEDS_BASE_URL.includes(current.provider) && (
                  <div className="space-y-1 md:col-span-2">
                    <label className="text-xs font-medium text-slate-600">
                      Base URL {current.provider === "ollama" ? "(e.g. http://localhost:11434)" : "(Azure endpoint)"}
                    </label>
                    <Input placeholder="https://…" />
                  </div>
                )}
              </div>

              {saveError && <p className="text-xs text-red-600">{saveError}</p>}
              {testResult && (
                <p className={`text-xs font-medium ${testResult.includes("success") ? "text-emerald-600" : "text-red-600"}`}>
                  {testResult}
                </p>
              )}

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={testConnection}
                  disabled={testing}
                >
                  {testing ? "Testing…" : "Test connection"}
                </Button>
                <Button
                  onClick={() => save.mutate()}
                  disabled={save.isPending}
                >
                  {save.isPending ? "Saving…" : "Save changes"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
