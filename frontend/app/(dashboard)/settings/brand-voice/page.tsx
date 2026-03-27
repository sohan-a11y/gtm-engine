"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { fetchJson, submitJson } from "@/lib/api";

type BrandVoice = {
  tone: string;
  vocabulary: string[];
  banned_phrases: string[];
};

const TONE_OPTIONS = ["professional", "casual", "consultative", "direct", "empathetic", "bold"];

export default function BrandVoicePage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<BrandVoice | null>(null);
  const [vocabInput, setVocabInput] = useState("");
  const [bannedInput, setBannedInput] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const { data: voice, isLoading } = useQuery<BrandVoice>({
    queryKey: ["settings-brand-voice"],
    queryFn: () => fetchJson<BrandVoice>("/settings/brand-voice", {
      tone: "professional",
      vocabulary: [],
      banned_phrases: [],
    }),
  });

  const current = form ?? voice ?? { tone: "professional", vocabulary: [], banned_phrases: [] };

  function patch(updates: Partial<BrandVoice>) {
    setForm((prev) => ({ ...(prev ?? current), ...updates }));
  }

  const save = useMutation({
    mutationFn: async () => {
      const result = await submitJson("/settings/brand-voice", current, { method: "PATCH" });
      if (!result.ok) throw new Error("Save failed");
      return result.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings-brand-voice"] });
      setForm(null);
      setSaveError(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
    onError: (e: Error) => setSaveError(e.message),
  });

  function addVocab() {
    const word = vocabInput.trim();
    if (!word || current.vocabulary.includes(word)) return;
    patch({ vocabulary: [...current.vocabulary, word] });
    setVocabInput("");
  }

  function removeVocab(w: string) {
    patch({ vocabulary: current.vocabulary.filter((v) => v !== w) });
  }

  function addBanned() {
    const phrase = bannedInput.trim();
    if (!phrase || current.banned_phrases.includes(phrase)) return;
    patch({ banned_phrases: [...current.banned_phrases, phrase] });
    setBannedInput("");
  }

  function removeBanned(p: string) {
    patch({ banned_phrases: current.banned_phrases.filter((b) => b !== p) });
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/" },
          { label: "Settings", href: "/settings" },
          { label: "Brand voice" },
        ]}
      />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Brand voice</p>
            <h1 className="font-display text-3xl font-semibold">
              Teach the outbound agent how you sound
            </h1>
          </div>

          {isLoading ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : (
            <div className="space-y-5">
              {/* Tone */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600">Tone</label>
                <div className="flex flex-wrap gap-2">
                  {TONE_OPTIONS.map((t) => (
                    <button
                      key={t}
                      onClick={() => patch({ tone: t })}
                      className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                        current.tone === t
                          ? "bg-primary text-white"
                          : "border border-border bg-white text-slate-600 hover:border-primary/50"
                      }`}
                    >
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Preferred vocabulary */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600">
                  Preferred vocabulary
                  <span className="ml-1 font-normal text-slate-400">(words to use more often)</span>
                </label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add a word or phrase…"
                    value={vocabInput}
                    onChange={(e) => setVocabInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addVocab()}
                  />
                  <Button variant="outline" size="sm" onClick={addVocab}>Add</Button>
                </div>
                {current.vocabulary.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {current.vocabulary.map((w) => (
                      <span
                        key={w}
                        className="flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs text-emerald-700"
                      >
                        {w}
                        <button
                          onClick={() => removeVocab(w)}
                          className="ml-0.5 text-emerald-500 hover:text-emerald-700"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Banned phrases */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-600">
                  Banned phrases
                  <span className="ml-1 font-normal text-slate-400">(words to avoid)</span>
                </label>
                <div className="flex gap-2">
                  <Input
                    placeholder="synergy, leverage, disruptive…"
                    value={bannedInput}
                    onChange={(e) => setBannedInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addBanned()}
                  />
                  <Button variant="outline" size="sm" onClick={addBanned}>Add</Button>
                </div>
                {current.banned_phrases.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {current.banned_phrases.map((p) => (
                      <span
                        key={p}
                        className="flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs text-red-700"
                      >
                        {p}
                        <button
                          onClick={() => removeBanned(p)}
                          className="ml-0.5 text-red-400 hover:text-red-600"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {saveError && <p className="text-xs text-red-600">{saveError}</p>}
              {saved && <p className="text-xs text-emerald-600 font-medium">Voice profile saved.</p>}

              <Button onClick={() => save.mutate()} disabled={save.isPending}>
                {save.isPending ? "Saving…" : "Save voice profile"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
