import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const steps = [
  "Create workspace",
  "Connect CRM",
  "Import leads",
  "Train ICP",
  "Review first draft"
];

export default function OnboardingPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Onboarding" }]} />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Onboarding wizard</p>
              <h1 className="font-display text-3xl font-semibold">Set up the workspace in five steps</h1>
            </div>
            <Badge tone="primary">Step 1 of 5</Badge>
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            {steps.map((step, index) => (
              <div key={step} className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Step {index + 1}</p>
                <p className="mt-2 font-semibold">{step}</p>
              </div>
            ))}
          </div>
          <Button>Continue</Button>
        </CardContent>
      </Card>
    </div>
  );
}
