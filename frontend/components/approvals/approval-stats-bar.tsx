import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export function ApprovalStatsBar({
  pending,
  approved,
  rejected
}: {
  pending: number;
  approved: number;
  rejected: number;
}) {
  const items = [
    { label: "Pending", value: pending, tone: "warning" as const },
    { label: "Approved", value: approved, tone: "success" as const },
    { label: "Rejected", value: rejected, tone: "danger" as const }
  ];

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="font-display text-3xl font-semibold">{item.value}</p>
            </div>
            <Badge tone={item.tone}>{item.label}</Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
