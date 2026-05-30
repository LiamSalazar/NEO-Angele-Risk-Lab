import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-md border border-cyan-300/15 bg-slate-950/55 px-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/45 focus:ring-2 focus:ring-cyan-300/15",
        className
      )}
      {...props}
    />
  );
}
