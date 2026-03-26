import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export default function NewCampaignPage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Campaigns", href: "/campaigns" }, { label: "New" }]} />
      <Card>
        <CardContent className="space-y-5 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Campaign wizard</p>
            <h1 className="font-display text-3xl font-semibold">Create a review-ready outbound motion</h1>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input placeholder="Campaign name" defaultValue="Founder-led Expansion" />
            <Input placeholder="ICP threshold" defaultValue="0.7" />
            <Input placeholder="Tone" defaultValue="Direct, consultative" />
            <Input placeholder="Value proposition" defaultValue="Shorten the time from signal to meeting." />
          </div>
          <Textarea placeholder="Campaign brief" defaultValue="Use high-intent leads only. Draft three variants and require approval before send." />
          <div className="flex flex-wrap gap-2">
            <Button>Create campaign</Button>
            <Button variant="outline">Save as draft</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
