"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/hooks/use-auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();
  const [pending, startTransition] = useTransition();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="grid w-full max-w-6xl gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <section className="glass-panel panel-ring relative overflow-hidden rounded-[2rem] border border-border/80 p-8 shadow-soft">
        <div className="absolute inset-0 soft-grid opacity-35" />
        <div className="relative space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            <Sparkles className="h-3.5 w-3.5" />
            AI GTM Engine
          </div>
          <div className="max-w-2xl space-y-4">
            <h1 className="font-display text-5xl font-semibold tracking-tight text-balance">
              One workspace for scoring, drafting, reviewing, and launching revenue motion.
            </h1>
            <p className="max-w-xl text-lg leading-8 text-slate-600">
              Artifex replaces disconnected GTM tooling with an opinionated orchestration layer for leads,
              campaigns, approvals, and live agent workflows.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["Lead scoring", "0.86 ICP"],
              ["Draft review", "3 variants"],
              ["Live orchestration", "SSE enabled"]
            ].map(([label, value]) => (
              <Card key={label} className="bg-white/85">
                <CardContent className="p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
                  <p className="mt-2 font-display text-2xl font-semibold">{value}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <Card className="self-center">
        <CardContent className="space-y-5 p-8">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Sign in</p>
            <h2 className="font-display text-3xl font-semibold">Welcome back</h2>
            <p className="text-sm text-slate-600">Use your workspace credentials to sign in.</p>
          </div>

          <div className="space-y-4">
            <label className="block space-y-2">
              <span className="text-sm font-medium">Email</span>
              <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-medium">Password</span>
              <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
            </label>
          </div>

          {error ? <p className="text-sm text-danger">{error}</p> : null}

          <Button
            className="w-full"
            disabled={pending}
            onClick={() => {
              startTransition(() => {
                void login({ email, password })
                  .then(() => router.push("/"))
                  .catch((caughtError: unknown) => setError(caughtError instanceof Error ? caughtError.message : "Login failed"));
              });
            }}
          >
            {pending ? "Signing in..." : "Enter workspace"}
            <ArrowRight className="h-4 w-4" />
          </Button>

          <p className="text-sm text-slate-500">
            Already have a session?{" "}
            <Link href="/" className="font-semibold text-primary">
              Jump back into the workspace
            </Link>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
