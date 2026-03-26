"use client";

import { Bell, ChevronsLeftRight, Search, Sparkles } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/hooks/use-auth";
import { useAppStore } from "@/lib/store";

export function Header() {
  const { user, orgName, logout } = useAuth();
  const collapsed = useAppStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useAppStore((state) => state.toggleSidebar);
  const setLeadSearch = useAppStore((state) => state.setLeadSearch);
  const query = useAppStore((state) => state.leadSearch);

  return (
    <header className="glass-panel panel-ring flex flex-col gap-4 rounded-3xl border border-border/80 px-4 py-4 shadow-soft lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" onClick={toggleSidebar}>
          <ChevronsLeftRight className="h-4 w-4" />
          {collapsed ? "Expand" : "Collapse"}
        </Button>
        <div>
          <div className="flex items-center gap-2">
            <Badge tone="primary" className="border-0">
              {orgName}
            </Badge>
            <span className="text-sm text-slate-500">Revenue ops workspace</span>
          </div>
          <p className="font-display text-xl font-semibold tracking-tight">Orchestrate the next best move</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 lg:max-w-2xl lg:flex-row lg:items-center lg:justify-end">
        <div className="relative w-full lg:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            className="pl-9"
            placeholder="Search leads, campaigns, or approvals"
            value={query}
            onChange={(event) => {
              const value = event.target.value;
              setLeadSearch(value);
            }}
          />
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Sparkles className="h-4 w-4" />
            Quick action
          </Button>
          <Button variant="outline" size="sm">
            <Bell className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3 rounded-2xl border border-border bg-white px-3 py-2">
            <Avatar src={user?.avatarUrl} alt={user?.name ?? "User"} fallback={user?.name?.slice(0, 2) ?? "U"} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{user?.name ?? "Revenue operator"}</p>
              <p className="truncate text-xs text-slate-500">{user?.email ?? "ready@artifex.ai"}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => void logout()}>
              Sign out
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
