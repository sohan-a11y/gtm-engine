"use client";

import { CartesianGrid, Line, LineChart as ReLineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function LineChart({
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
          <ReLineChart data={data}>
            <CartesianGrid strokeDasharray="4 4" stroke="rgba(148, 163, 184, 0.18)" />
            <XAxis dataKey={xKey} stroke="rgba(100, 116, 139, 0.9)" />
            <YAxis stroke="rgba(100, 116, 139, 0.9)" />
            <Tooltip />
            <Line type="monotone" dataKey={dataKey} stroke="hsl(var(--accent))" strokeWidth={3} dot={false} />
          </ReLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
