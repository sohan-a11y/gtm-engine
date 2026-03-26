import { cloneElement, isValidElement, type ButtonHTMLAttributes, type ReactElement } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "ghost" | "destructive" | "outline";
  size?: "sm" | "md" | "lg";
  asChild?: boolean;
};

const variants: Record<NonNullable<ButtonProps["variant"]>, string> = {
  default:
    "bg-primary text-primary-foreground shadow-soft hover:translate-y-[-1px] hover:shadow-panel",
  secondary: "bg-muted text-foreground hover:bg-muted/80",
  ghost: "bg-transparent hover:bg-muted/70",
  destructive: "bg-danger text-danger-foreground hover:opacity-90",
  outline: "border border-border bg-card hover:bg-muted/60"
};

const sizes: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-5 text-base"
};

export function Button({
  className,
  variant = "default",
  size = "md",
  asChild,
  children,
  ...props
}: ButtonProps) {
  const styles = cn(
    "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
    variants[variant],
    sizes[size],
    className
  );

  if (asChild && isValidElement(children)) {
    return cloneElement(children as ReactElement<{ className?: string }>, {
      className: cn(styles, children.props.className)
    });
  }

  return (
    <button
      className={styles}
      {...props}
    >
      {children}
    </button>
  );
}
