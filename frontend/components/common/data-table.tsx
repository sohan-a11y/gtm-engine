"use client";

import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import { ArrowUpDown, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableCell, TableHeadCell, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

export type Column<T> = {
  key: string;
  header: string;
  accessor: (row: T) => ReactNode;
  sortable?: boolean;
  sortValue?: (row: T) => string | number;
  className?: string;
};

export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = "Search",
  searchable,
  onRowClick,
  emptyLabel = "No records found",
  toolbar
}: {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  searchable?: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyLabel?: string;
  toolbar?: ReactNode;
}) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const filtered = useMemo(() => {
    const search = query.trim().toLowerCase();
    let rows = [...data];

    if (search && searchable) {
      rows = rows.filter((row) => searchable(row).toLowerCase().includes(search));
    }

    if (sortKey) {
      const column = columns.find((item) => item.key === sortKey);
      if (column?.sortValue) {
        rows.sort((a, b) => {
          const left = column.sortValue?.(a);
          const right = column.sortValue?.(b);
          if (left === right) return 0;
          if (typeof left === "number" && typeof right === "number") {
            return sortDirection === "asc" ? left - right : right - left;
          }
          return sortDirection === "asc"
            ? String(left).localeCompare(String(right))
            : String(right).localeCompare(String(left));
        });
      }
    }

    return rows;
  }, [columns, data, query, searchable, sortDirection, sortKey]);

  return (
    <Card>
      <CardContent className="space-y-4 p-0">
        <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pl-9"
              placeholder={searchPlaceholder}
            />
          </div>
          <div className="flex items-center gap-2">
            {toolbar}
            <Badge tone="neutral">{filtered.length} records</Badge>
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <thead className="bg-muted/40">
              <tr>
                {columns.map((column) => (
                  <TableHeadCell key={column.key} className={column.className}>
                    <button
                      type="button"
                      onClick={() => {
                        if (!column.sortable) {
                          return;
                        }
                        if (sortKey === column.key) {
                          setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
                        } else {
                          setSortKey(column.key);
                          setSortDirection("asc");
                        }
                      }}
                      className={cn(
                        "inline-flex items-center gap-1 text-left",
                        column.sortable ? "cursor-pointer hover:text-foreground" : "cursor-default"
                      )}
                    >
                      {column.header}
                      {column.sortable ? <ArrowUpDown className="h-3 w-3" /> : null}
                    </button>
                  </TableHeadCell>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, index) => (
                <TableRow
                  key={index}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(onRowClick ? "cursor-pointer" : "", "bg-white")}
                >
                  {columns.map((column) => (
                    <TableCell key={column.key} className={column.className}>
                      {column.accessor(row)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </tbody>
          </Table>
        </div>

        {filtered.length === 0 ? (
          <div className="border-t border-border p-6 text-center text-sm text-slate-500">{emptyLabel}</div>
        ) : null}
      </CardContent>
    </Card>
  );
}
