"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { fetchJson, submitJson } from "@/lib/api";

type TeamMember = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
};

const ROLE_TONES: Record<string, "success" | "primary" | "neutral" | "warning"> = {
  admin: "primary",
  member: "success",
  viewer: "neutral",
};

const ROLES = ["admin", "member", "viewer"];

export default function SettingsTeamPage() {
  const qc = useQueryClient();
  const [showInvite, setShowInvite] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteError, setInviteError] = useState<string | null>(null);

  const { data: members = [], isLoading } = useQuery<TeamMember[]>({
    queryKey: ["team"],
    queryFn: () => fetchJson<TeamMember[]>("/auth/users", []),
  });

  const invite = useMutation({
    mutationFn: async () => {
      const result = await submitJson("/auth/invite", {
        email: inviteEmail,
        full_name: inviteName || null,
        role: inviteRole,
      });
      if (!result.ok) throw new Error("Invite failed");
      return result.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["team"] });
      setShowInvite(false);
      setInviteEmail("");
      setInviteName("");
      setInviteRole("member");
      setInviteError(null);
    },
    onError: (e: Error) => setInviteError(e.message),
  });

  const updateRole = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      const result = await submitJson(
        `/auth/users/${userId}/role?role=${encodeURIComponent(role)}`,
        {},
        { method: "PATCH" }
      );
      if (!result.ok) throw new Error("Role update failed");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["team"] }),
  });

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
          { label: "Dashboard", href: "/" },
          { label: "Settings", href: "/settings" },
          { label: "Team" },
        ]}
      />
      <Card>
        <CardContent className="space-y-4 p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Team access</p>
              <h1 className="font-display text-3xl font-semibold">Manage roles and permissions</h1>
            </div>
            <Button variant="outline" onClick={() => setShowInvite((v) => !v)}>
              {showInvite ? "Cancel" : "Invite teammate"}
            </Button>
          </div>

          {/* Invite form */}
          {showInvite && (
            <div className="rounded-2xl border border-border bg-slate-50 p-4 space-y-3">
              <p className="font-semibold text-sm">Invite a new teammate</p>
              <div className="grid gap-3 md:grid-cols-3">
                <Input
                  placeholder="Work email"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
                <Input
                  placeholder="Full name (optional)"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                />
                <select
                  className="rounded-xl border border-border bg-white px-3 py-2 text-sm"
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r.charAt(0).toUpperCase() + r.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              {inviteError && (
                <p className="text-xs text-red-600">{inviteError}</p>
              )}
              <Button
                size="sm"
                disabled={!inviteEmail || invite.isPending}
                onClick={() => invite.mutate()}
              >
                {invite.isPending ? "Sending…" : "Send invite"}
              </Button>
            </div>
          )}

          {/* Member list */}
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading team…</p>
          ) : members.length === 0 ? (
            <p className="text-sm text-slate-500">No team members yet.</p>
          ) : (
            <div className="space-y-3">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between rounded-2xl border border-border bg-white p-4 gap-4"
                >
                  <div className="min-w-0">
                    <p className="font-semibold truncate">
                      {member.full_name || member.email}
                    </p>
                    {member.full_name && (
                      <p className="text-xs text-slate-500 truncate">{member.email}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <select
                      className="rounded-lg border border-border bg-white px-2 py-1 text-xs"
                      value={member.role}
                      onChange={(e) =>
                        updateRole.mutate({ userId: member.id, role: e.target.value })
                      }
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r.charAt(0).toUpperCase() + r.slice(1)}
                        </option>
                      ))}
                    </select>
                    <Badge tone={ROLE_TONES[member.role] ?? "neutral"}>
                      {member.role}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
