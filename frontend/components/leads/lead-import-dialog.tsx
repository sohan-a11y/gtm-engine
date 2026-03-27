"use client";

import { useRef, useState } from "react";
import { Upload, CheckCircle2, AlertCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

type ImportResult = {
  imported: number;
  skipped: number;
  duplicates: number;
  errors: number;
};

type PreviewRow = Record<string, string>;

export function LeadImportDialog() {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewRow[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const qc = useQueryClient();

  function parsePreview(text: string) {
    const lines = text.split("\n").filter(Boolean);
    if (lines.length === 0) return;
    const hdrs = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
    setHeaders(hdrs);
    const rows = lines.slice(1, 6).map((line) => {
      const vals = line.split(",").map((v) => v.trim().replace(/^"|"$/g, ""));
      return Object.fromEntries(hdrs.map((h, i) => [h, vals[i] ?? ""]));
    });
    setPreview(rows);
  }

  function handleFileChange(f: File | null) {
    setFile(f);
    setResult(null);
    setError(null);
    if (!f) return;
    const reader = new FileReader();
    reader.onload = (e) => parsePreview(e.target?.result as string);
    reader.readAsText(f);
  }

  async function handleImport() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("upload", file);
      const resp = await apiFetch("/leads/import", { method: "POST", body: form });
      if (!resp.ok) {
        setError(`Import failed (${resp.status})`);
        return;
      }
      const data: ImportResult = await resp.json();
      setResult(data);
      setFile(null);
      setPreview([]);
      setHeaders([]);
      await qc.invalidateQueries({ queryKey: ["leads"] });
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div>
          <CardTitle>Import leads</CardTitle>
          <p className="mt-1 text-sm text-slate-600">
            Upload a CSV with email, first_name, last_name, company_name, title columns.
          </p>
        </div>
        <Button variant="outline" onClick={() => { setOpen((c) => !c); setResult(null); setError(null); }}>
          <Upload className="h-4 w-4" />
          {open ? "Close" : "Open"} importer
        </Button>
      </CardHeader>

      {open && (
        <CardContent className="space-y-4">
          {/* Drop zone */}
          <div
            className="rounded-2xl border-2 border-dashed border-border bg-muted/30 p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFileChange(e.dataTransfer.files[0] ?? null);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
            />
            {file ? (
              <p className="font-semibold text-primary">{file.name}</p>
            ) : (
              <>
                <p className="font-semibold">Drop a CSV here or click to browse</p>
                <p className="mt-1 text-sm text-slate-500">Required column: email</p>
              </>
            )}
          </div>

          {/* Preview table */}
          {headers.length > 0 && preview.length > 0 && (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-xs">
                <thead className="bg-slate-50">
                  <tr>
                    {headers.map((h) => (
                      <th key={h} className="px-3 py-2 text-left font-semibold text-slate-600">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i} className="border-t border-border">
                      {headers.map((h) => (
                        <td key={h} className="px-3 py-2 text-slate-700 truncate max-w-[140px]">
                          {row[h]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="px-3 py-1 text-xs text-slate-400 border-t border-border">
                Showing first {preview.length} rows
              </p>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="flex items-start gap-2 rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">
              <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
              <span>
                Imported <strong>{result.imported}</strong> leads.
                {result.duplicates > 0 && <> {result.duplicates} duplicates skipped.</>}
                {result.errors > 0 && <> {result.errors} errors.</>}
              </span>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Button onClick={handleImport} disabled={!file || loading}>
            {loading ? "Importing…" : "Import leads"}
          </Button>
        </CardContent>
      )}
    </Card>
  );
}
