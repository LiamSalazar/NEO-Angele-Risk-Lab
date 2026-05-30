import { Slot } from "@radix-ui/react-slot";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "icon";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "border-cyan-300/35 bg-cyan-300/12 text-cyan-100 shadow-[0_0_22px_rgba(66,242,255,0.12)] hover:bg-cyan-300/18",
  secondary:
    "border-slate-500/30 bg-slate-200/7 text-slate-100 hover:border-cyan-300/35 hover:bg-slate-200/10",
  ghost: "border-transparent bg-transparent text-slate-300 hover:bg-white/7 hover:text-white",
  danger: "border-rose-300/35 bg-rose-300/10 text-rose-100 hover:bg-rose-300/16"
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  icon: "h-9 w-9 p-0"
};

export function Button({
  asChild,
  className,
  variant = "secondary",
  size = "md",
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md border font-medium transition focus:outline-none focus:ring-2 focus:ring-cyan-300/40 disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
