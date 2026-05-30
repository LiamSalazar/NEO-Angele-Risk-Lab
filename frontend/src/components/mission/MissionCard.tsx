import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type MissionCardProps = {
  label: string;
  value: string | number;
  detail?: string;
  icon: LucideIcon;
  tone?: "cyan" | "green" | "amber" | "red" | "neutral";
};

const tones = {
  cyan: "text-cyan-100 border-cyan-300/20 bg-cyan-300/8",
  green: "text-emerald-100 border-emerald-300/20 bg-emerald-300/8",
  amber: "text-amber-100 border-amber-300/20 bg-amber-300/8",
  red: "text-rose-100 border-rose-300/20 bg-rose-300/8",
  neutral: "text-slate-100 border-slate-300/15 bg-slate-300/8"
};

export function MissionCard({ label, value, detail, icon: Icon, tone = "cyan" }: MissionCardProps) {
  return (
    <Card className="min-h-[142px] overflow-hidden p-4">
      <CardContent className="flex h-full flex-col justify-between gap-5">
        <div className="flex items-center justify-between gap-3">
          <p className="technical-label text-[11px] text-slate-400">{label}</p>
          <span className={cn("grid h-9 w-9 place-items-center rounded-md border", tones[tone])}>
            <Icon className="h-4 w-4" />
          </span>
        </div>
        <div>
          <p className="font-mono text-3xl font-semibold text-white">{value}</p>
          {detail ? <p className="mt-1 text-sm text-slate-400">{detail}</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}
