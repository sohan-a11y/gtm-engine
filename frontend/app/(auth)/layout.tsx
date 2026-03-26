import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="absolute inset-0 soft-grid opacity-40" />
      <div className="absolute left-[-10%] top-[-10%] h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="absolute right-[-8%] top-[10%] h-80 w-80 rounded-full bg-accent/10 blur-3xl" />
      <div className="relative mx-auto flex min-h-screen max-w-7xl items-center justify-center px-4 py-10">
        {children}
      </div>
    </div>
  );
}
