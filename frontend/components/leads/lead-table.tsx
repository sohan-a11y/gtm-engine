import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/common/data-table";
import { IcpScoreBadge } from "@/components/leads/icp-score-badge";
import type { Lead } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const columns: Column<Lead>[] = [
  {
    key: "lead",
    header: "Lead",
    accessor: (lead) => (
      <div>
        <p className="font-semibold">{lead.name}</p>
        <p className="text-xs text-slate-500">
          {lead.title} at {lead.company}
        </p>
      </div>
    ),
    sortable: true,
    sortValue: (lead) => lead.name
  },
  {
    key: "score",
    header: "ICP",
    accessor: (lead) => <IcpScoreBadge score={lead.icpScore} />,
    sortable: true,
    sortValue: (lead) => lead.icpScore
  },
  {
    key: "status",
    header: "Status",
    accessor: (lead) => <Badge tone="neutral">{lead.status}</Badge>
  },
  {
    key: "owner",
    header: "Owner",
    accessor: (lead) => lead.owner
  },
  {
    key: "updated",
    header: "Updated",
    accessor: (lead) => formatDate(lead.lastTouchedAt),
    sortable: true,
    sortValue: (lead) => new Date(lead.lastTouchedAt).getTime()
  }
];

export function LeadTable({
  data,
  onRowClick
}: {
  data: Lead[];
  onRowClick?: (lead: Lead) => void;
}) {
  return (
    <DataTable
      data={data}
      columns={columns}
      searchable={(lead) => [lead.name, lead.company, lead.title, lead.email, lead.notes].join(" ")}
      searchPlaceholder="Search leads"
      onRowClick={onRowClick}
      emptyLabel="No leads matched your search."
    />
  );
}
