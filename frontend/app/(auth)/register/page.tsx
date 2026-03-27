"use client";

import { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/hooks/use-auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthenticated } = useAuth();
  const [pending, startTransition] = useTransition();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [orgName, setOrgName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, router]);

  function handleSubmit() {
    setError(null);
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    startTransition(() => {
      void register({
        email,
        password,
        full_name: fullName || undefined,
        org_name: orgName || undefined,
      })
        .then(() => router.push("/"))
        .catch((err: unknown) =>
          setError(err instanceof Error ? err.message : "Registration failed")
        );
    });
  }

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
              Start orchestrating your GTM motion with AI.
            </h1>
            <p className="max-w-xl text-lg leading-8 text-slate-600">
              Set up your workspace in seconds. Bring your own CRM credentials and LLM keys — everything else is built in.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["Setup time", "< 2 min"],
              ["Integrations", "HubSpot · SF"],
              ["Agents", "ICP · Outbound"],
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
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Create account</p>
            <h2 className="font-display text-3xl font-semibold">Get started free</h2>
            <p className="text-sm text-slate-600">Create your workspace to start scoring leads and drafting campaigns.</p>
          </div>

          <div className="space-y-4">
            <label className="block space-y-2">
              <span className="text-sm font-medium">Full Name</span>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                type="text"
                placeholder="Jane Smith"
              />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-medium">Work Email</span>
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="jane@company.com"
              />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-medium">Company Name <span className="text-slate-400">(optional)</span></span>
              <Input
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                type="text"
                placeholder="Acme Corp"
              />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-medium">Password</span>
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                placeholder="Min. 8 characters"
              />
            </label>
            <label className="block space-y-2">
              <span className="text-sm font-medium">Confirm Password</span>
              <Input
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                type="password"
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              />
            </label>
          </div>

          {error ? <p className="text-sm text-danger">{error}</p> : null}

          <Button className="w-full" disabled={pending} onClick={handleSubmit}>
            {pending ? "Creating workspace..." : "Create workspace"}
            <ArrowRight className="h-4 w-4" />
          </Button>

          <p className="text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-primary">
              Sign in
            </Link>
            .
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
