import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { ApprovalItem } from "@/lib/types";

export function ApprovalList({
  items,
  selectedId,
  onSelect
}: {
  items: ApprovalItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Review queue</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.id)}
            className="block w-full text-left"
          >
            <div
              className={`rounded-2xl border p-4 transition ${
                selectedId === item.id ? "border-primary bg-primary/5 shadow-soft" : "border-border bg-white hover:bg-muted/40"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{item.lead.name}</p>
                  <p className="text-sm text-slate-500">{item.lead.company}</p>
                </div>
                <Badge tone="warning">{item.status}</Badge>
              </div>
              <p className="mt-2 text-sm text-slate-600">Campaign: {item.campaign}</p>
              <p className="mt-1 text-xs text-slate-500">{formatDate(item.createdAt)}</p>
              <span className="mt-3 inline-flex h-8 w-full items-center justify-center rounded-xl border border-border bg-white text-sm font-medium">
                Open review
              </span>
            </div>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
