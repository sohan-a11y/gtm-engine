import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { mockCompanies } from "@/lib/mock-data";
import { formatDate } from "@/lib/utils";

export default function CompanyDetailPage({ params }: { params: { id: string } }) {
  const company = mockCompanies.find((entry) => entry.id === params.id);

  if (!company) {
    notFound();
  }

  return (
    <div className="space-y-4">
      <Breadcrumbs
        items={[
        { label: "Dashboard", href: "/" },
          { label: "Companies", href: "/companies" },
          { label: company.name }
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="font-display text-3xl font-semibold">{company.name}</h1>
                <p className="text-sm text-slate-500">{company.domain}</p>
              </div>
              <Badge tone="success">{Math.round(company.healthScore * 100)}% health</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Owner</p>
                <p className="mt-1 font-semibold">{company.owner}</p>
              </div>
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Revenue</p>
                <p className="mt-1 font-semibold">{company.revenue}</p>
              </div>
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Employees</p>
                <p className="mt-1 font-semibold">{company.employees}</p>
              </div>
              <div className="rounded-2xl border border-border bg-white p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Last sync</p>
                <p className="mt-1 font-semibold">{formatDate(company.lastSyncAt)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-3 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Health notes</p>
            <p className="font-display text-2xl font-semibold">A healthy account is ready for multi-threaded outreach.</p>
            <p className="text-sm text-slate-600">
              This page will eventually surface team members, historical activity, and campaign attribution.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
