import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function IcpScoreBadge({ score }: { score: number }) {
  const tone = score >= 0.7 ? "success" : score >= 0.4 ? "warning" : "danger";

  return (
    <Badge tone={tone} className={cn("min-w-[86px] justify-center")}>
      ICP {(score * 100).toFixed(0)}%
    </Badge>
  );
}
