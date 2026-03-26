import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SettingsLLMPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings", href: "/settings" }, { label: "LLM" }]} />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">LLM configuration</p>
              <h1 className="font-display text-3xl font-semibold">Select provider, model, and fallback policy</h1>
            </div>
            <Badge tone="primary">Demo mode</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input defaultValue="OpenAI" placeholder="Provider" />
            <Input defaultValue="gpt-4.1-mini" placeholder="Model" />
          </div>
          <Button>Test connection</Button>
        </CardContent>
      </Card>
    </div>
  );
}
