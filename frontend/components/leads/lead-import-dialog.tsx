"use client";

import { useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function LeadImportDialog() {
  const [open, setOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div>
          <CardTitle>Import leads</CardTitle>
          <p className="mt-1 text-sm text-slate-600">Upload CSV, map fields, and queue enrichment.</p>
        </div>
        <Button variant="outline" onClick={() => setOpen((current) => !current)}>
          <Upload className="h-4 w-4" />
          {open ? "Close" : "Open"} importer
        </Button>
      </CardHeader>
      {open ? (
        <CardContent className="space-y-4">
          <div className="rounded-2xl border-2 border-dashed border-border bg-muted/30 p-6 text-center">
            <p className="font-semibold">Drop a CSV here</p>
            <p className="mt-1 text-sm text-slate-500">or connect a CRM sync during onboarding</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input placeholder="Name column" defaultValue="full_name" />
            <Input placeholder="Email column" defaultValue="email" />
          </div>
          <Textarea
            placeholder="Notes or mapping rules"
            defaultValue="Enrich only if email is verified and company has > 50 employees."
          />
        </CardContent>
      ) : null}
    </Card>
  );
}
