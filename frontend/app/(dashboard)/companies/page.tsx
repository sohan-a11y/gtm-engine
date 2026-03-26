"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { DataTable, type Column } from "@/components/common/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCompanies } from "@/lib/hooks/use-companies";
import type { Company } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const columns: Column<Company>[] = [
  { key: "name", header: "Company", accessor: (company) => company.name, sortable: true, sortValue: (company) => company.name },
  { key: "industry", header: "Industry", accessor: (company) => company.industry },
  { key: "health", header: "Health", accessor: (company) => <Badge tone="success">{Math.round(company.healthScore * 100)}%</Badge>, sortable: true, sortValue: (company) => company.healthScore },
  { key: "owner", header: "Owner", accessor: (company) => company.owner },
  { key: "sync", header: "Last sync", accessor: (company) => formatDate(company.lastSyncAt) }
];

export default function CompaniesPage() {
  const companies = useCompanies();
  const router = useRouter();

  return (
    <div className="space-y-4">
      <Breadcrumbs items={[{ label: "Dashboard", href: "/" }, { label: "Companies" }]} />
      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardContent className="space-y-4 p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Account view</p>
                <h1 className="font-display text-3xl font-semibold">Monitor company health and coverage</h1>
              </div>
              <Button asChild>
                <Link href="/campaigns">
                  Campaigns
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            <DataTable
              data={companies.data ?? []}
              columns={columns}
              searchable={(company) => [company.name, company.domain, company.industry].join(" ")}
              onRowClick={(company) => router.push(`/companies/${company.id}`)}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-3 p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Snapshot</p>
            <p className="font-display text-2xl font-semibold">Healthy accounts are the best expansion surface.</p>
            <p className="text-sm text-slate-600">
              This scaffold keeps company health, sync freshness, and ownership visible so account plans can be prioritized fast.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
