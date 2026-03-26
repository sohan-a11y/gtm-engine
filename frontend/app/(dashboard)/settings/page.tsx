import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings" }]} />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Workspace settings</p>
              <h1 className="font-display text-3xl font-semibold">General configuration</h1>
            </div>
            <Badge tone="primary">Admin</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input defaultValue="Artifex" placeholder="Workspace name" />
            <Input defaultValue="Revenue ops" placeholder="Industry" />
          </div>
          <Button>Save changes</Button>
        </CardContent>
      </Card>
    </div>
  );
}
