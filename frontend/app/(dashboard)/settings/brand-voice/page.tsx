import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function BrandVoicePage() {
  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Settings", href: "/settings" }, { label: "Brand voice" }]} />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Brand voice</p>
            <h1 className="font-display text-3xl font-semibold">Teach the outbound agent how you sound</h1>
          </div>
          <Textarea defaultValue="We are clear, consultative, and direct. We avoid hype and keep CTAs specific." />
          <Button>Save voice profile</Button>
        </CardContent>
      </Card>
    </div>
  );
}
