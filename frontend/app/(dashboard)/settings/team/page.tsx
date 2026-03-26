import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const team = [
  ["Samir Rao", "admin"],
  ["Maya Patel", "member"],
  ["Owen Reed", "viewer"]
];

export default function SettingsTeamPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings", href: "/settings" }, { label: "Team" }]} />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Team access</p>
            <h1 className="font-display text-3xl font-semibold">Manage roles and permissions</h1>
          </div>
          <div className="space-y-3">
            {team.map(([name, role]) => (
              <div key={name} className="flex items-center justify-between rounded-2xl border border-border bg-white p-4">
                <div>
                  <p className="font-semibold">{name}</p>
                  <p className="text-sm text-slate-500">{role}</p>
                </div>
                <Badge tone="neutral">{role}</Badge>
              </div>
            ))}
          </div>
          <Button variant="outline">Invite teammate</Button>
        </CardContent>
      </Card>
    </div>
  );
}
