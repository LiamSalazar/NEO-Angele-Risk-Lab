import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
};

export function PageHeader({ eyebrow, title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between", className)}>
      <div className="max-w-3xl">
        {eyebrow ? <p className="technical-label text-xs text-cyan-100">{eyebrow}</p> : null}
        <h1 className="mt-2 text-3xl font-semibold tracking-normal text-white md:text-4xl">{title}</h1>
        {description ? <p className="mt-3 leading-7 text-slate-300">{description}</p> : null}
      </div>
      {actions ? <div className="shrink-0">{actions}</div> : null}
    </div>
  );
}
