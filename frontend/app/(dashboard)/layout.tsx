import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { DashboardShell } from "@/components/layout/dashboard-shell";

function hasRefreshCookie() {
  const jar = cookies();
  return Boolean(
    jar.get("refresh_token") ||
      jar.get("gtm_refresh_token") ||
      jar.get("__Host-refresh_token") ||
      jar.get("__Host-gtm_refresh_token")
  );
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  if (!hasRefreshCookie() && process.env.NEXT_PUBLIC_DEMO_MODE === "false") {
    redirect("/login");
  }

  return (
    <div className="min-h-screen">
      <DashboardShell>{children}</DashboardShell>
    </div>
  );
}
