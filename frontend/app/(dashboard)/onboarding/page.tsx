"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { fetchJson } from "@/lib/api";
import { unwrapItems } from "@/lib/transforms";

type ChecklistStep = {
  id: string;
  label: string;
  description: string;
  cta: string;
  href: string;
  done: boolean;
};

export default function OnboardingPage() {
  const { data: integrations = [] } = useQuery<any[]>({
    queryKey: ["integrations"],
    queryFn: async () => unwrapItems((await fetchJson<unknown>("/integrations", [])) as any),
  });

  const { data: leads = [] } = useQuery<any[]>({
    queryKey: ["leads"],
    queryFn: async () => unwrapItems((await fetchJson<unknown>("/leads?limit=1", [])) as any),
  });

  const { data: campaigns = [] } = useQuery<any[]>({
    queryKey: ["campaigns"],
    queryFn: async () => unwrapItems((await fetchJson<unknown>("/campaigns?limit=1", [])) as any),
  });

  const { data: approvals = [] } = useQuery<any[]>({
    queryKey: ["approvals"],
    queryFn: async () => unwrapItems((await fetchJson<unknown>("/approvals?limit=1", [])) as any),
  });

  const hasCrm = integrations.some(
    (i: any) => ["hubspot", "salesforce"].includes(i.provider) && i.status === "connected"
  );

  const steps: ChecklistStep[] = useMemo(
    () => [
      {
        id: "workspace",
        label: "Create your workspace",
        description: "Your organization is set up and ready to go.",
        cta: "Done",
        href: "/settings",
        done: true, // always true — they're logged in
      },
      {
        id: "crm",
        label: "Connect your CRM",
        description: "Link HubSpot or Salesforce to import contacts and deals automatically.",
        cta: hasCrm ? "View integrations" : "Connect CRM",
        href: "/settings/integrations",
        done: hasCrm,
      },
      {
        id: "leads",
        label: "Import leads",
        description: "Add your first contacts — manually, via CSV, or from your CRM sync.",
        cta: leads.length > 0 ? "View leads" : "Add first lead",
        href: "/leads",
        done: leads.length > 0,
      },
      {
        id: "campaign",
        label: "Create a campaign",
        description: "Define your ICP, tone, and value proposition for outbound messaging.",
        cta: campaigns.length > 0 ? "View campaigns" : "New campaign",
        href: "/campaigns",
        done: campaigns.length > 0,
      },
      {
        id: "approval",
        label: "Review your first draft",
        description: "Approve or tweak an AI-generated email sequence before it sends.",
        cta: approvals.length > 0 ? "Review now" : "Go to approvals",
        href: "/approvals",
        done: approvals.length > 0,
      },
    ],
    [hasCrm, leads, campaigns, approvals]
  );

  const completed = steps.filter((s) => s.done).length;
  const percent = Math.round((completed / steps.length) * 100);
  const nextStep = steps.find((s) => !s.done);

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Onboarding" }]} />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Onboarding wizard</p>
              <h1 className="font-display text-3xl font-semibold">
                Set up the workspace in five steps
              </h1>
            </div>
            <Badge tone={completed === steps.length ? "success" : "primary"}>
              {completed} of {steps.length} done
            </Badge>
          </div>

          <div className="space-y-1">
            <Progress value={percent} className="h-2" />
            <p className="text-xs text-slate-400">{percent}% complete</p>
          </div>

          <div className="space-y-3">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`rounded-2xl border p-4 flex items-center justify-between gap-4 ${
                  step.done
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-border bg-white"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      step.done
                        ? "bg-emerald-500 text-white"
                        : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {step.done ? "✓" : index + 1}
                  </div>
                  <div>
                    <p className={`font-semibold text-sm ${step.done ? "text-emerald-700" : ""}`}>
                      {step.label}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
                  </div>
                </div>
                <Link href={step.href}>
                  <Button
                    size="sm"
                    variant={step.done ? "outline" : "default"}
                  >
                    {step.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>

          {nextStep && (
            <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-sm">
              <p className="text-slate-500">
                <span className="font-semibold text-slate-800">Next up: </span>
                {nextStep.label} — {nextStep.description}
              </p>
              <Link href={nextStep.href}>
                <Button size="sm" className="mt-3">
                  {nextStep.cta}
                </Button>
              </Link>
            </div>
          )}

          {completed === steps.length && (
            <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-sm text-emerald-700 font-semibold text-center">
              🎉 You&apos;re all set! Your GTM engine is live.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
