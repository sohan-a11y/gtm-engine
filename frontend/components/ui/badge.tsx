import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "success" | "warning" | "danger" | "primary";
};

const tones: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-muted text-foreground",
  success: "bg-success/12 text-success border-success/20",
  warning: "bg-warning/14 text-warning-foreground border-warning/20",
  danger: "bg-danger/12 text-danger border-danger/20",
  primary: "bg-primary/12 text-primary border-primary/20"
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold tracking-wide",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}
