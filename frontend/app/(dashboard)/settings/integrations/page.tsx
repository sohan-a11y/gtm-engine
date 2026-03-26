import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const integrations = [
  ["HubSpot", "Connected"],
  ["Salesforce", "Disconnected"],
  ["Slack", "Connected"],
  ["Apollo", "Connected"]
];

export default function SettingsIntegrationsPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings", href: "/settings" }, { label: "Integrations" }]} />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Connections</p>
            <h1 className="font-display text-3xl font-semibold">Manage CRM, email, and enrichment providers</h1>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {integrations.map(([name, status]) => (
              <div key={name} className="rounded-2xl border border-border bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{name}</p>
                  <Badge tone={status === "Connected" ? "success" : "warning"}>{status}</Badge>
                </div>
              </div>
            ))}
          </div>
          <Button variant="outline">Add integration</Button>
        </CardContent>
      </Card>
    </div>
  );
}
