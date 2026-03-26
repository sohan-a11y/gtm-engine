import { Card, CardContent } from "@/components/ui/card";

export function MetricCard({
  label,
  value,
  delta
}: {
  label: string;
  value: string;
  delta?: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-2 p-5">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="font-display text-3xl font-semibold tracking-tight">{value}</p>
        {delta ? <p className="text-xs text-success">{delta}</p> : null}
      </CardContent>
    </Card>
  );
}
