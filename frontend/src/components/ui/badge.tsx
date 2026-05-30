import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "neutral" | "cyan" | "green" | "amber" | "red";

const variants: Record<BadgeVariant, string> = {
  neutral: "border-slate-400/25 bg-slate-300/8 text-slate-200",
  cyan: "border-cyan-300/30 bg-cyan-300/10 text-cyan-100",
  green: "border-emerald-300/30 bg-emerald-300/10 text-emerald-100",
  amber: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  red: "border-rose-300/35 bg-rose-300/10 text-rose-100"
};

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
};

export function Badge({ className, variant = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
