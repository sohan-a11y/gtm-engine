import Image from "next/image";

import { cn } from "@/lib/utils";

export function Avatar({
  src,
  alt,
  className,
  fallback
}: {
  src?: string;
  alt: string;
  className?: string;
  fallback: string;
}) {
  return (
    <div
      className={cn(
        "flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-muted text-sm font-semibold text-slate-700",
        className
      )}
    >
      {src ? <Image src={src} alt={alt} width={40} height={40} className="h-full w-full object-cover" /> : fallback}
    </div>
  );
}
