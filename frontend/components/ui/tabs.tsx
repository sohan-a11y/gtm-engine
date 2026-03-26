"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { cn } from "@/lib/utils";

type TabItem = {
  value: string;
  label: string;
  content: ReactNode;
};

export function Tabs({ items, defaultValue }: { items: TabItem[]; defaultValue?: string }) {
  const [active, setActive] = useState(defaultValue ?? items[0]?.value ?? "");
  const current = items.find((item) => item.value === active) ?? items[0];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 rounded-2xl border border-border bg-white p-2">
        {items.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => setActive(item.value)}
            className={cn(
              "rounded-xl px-4 py-2 text-sm font-medium transition",
              active === item.value
                ? "bg-primary text-primary-foreground shadow-soft"
                : "text-slate-600 hover:bg-muted"
            )}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div>{current?.content}</div>
    </div>
  );
}
