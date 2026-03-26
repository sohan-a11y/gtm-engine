"use client";

import { Bar, BarChart as ReBarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function BarChart({
  title,
  data,
  dataKey,
  xKey
}: {
  title: string;
  data: Array<Record<string, string | number>>;
  dataKey: string;
  xKey: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ReBarChart data={data}>
            <CartesianGrid strokeDasharray="4 4" stroke="rgba(148, 163, 184, 0.18)" />
            <XAxis dataKey={xKey} stroke="rgba(100, 116, 139, 0.9)" />
            <YAxis stroke="rgba(100, 116, 139, 0.9)" />
            <Tooltip />
            <Bar dataKey={dataKey} fill="hsl(var(--primary))" radius={[12, 12, 0, 0]} />
          </ReBarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
