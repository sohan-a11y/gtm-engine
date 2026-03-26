"use client";

import type { ReactNode } from "react";

import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { useAppStore } from "@/lib/store";

export function DashboardShell({ children }: { children: ReactNode }) {
  const collapsed = useAppStore((state) => state.sidebarCollapsed);

  return (
    <div className="mx-auto flex max-w-[1800px] gap-4 px-4 py-4 lg:px-6">
      <Sidebar collapsed={collapsed} />
      <main className="min-w-0 flex-1 space-y-4">
        <Header />
        <div className="space-y-4">{children}</div>
      </main>
    </div>
  );
}
