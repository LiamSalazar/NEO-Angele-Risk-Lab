import { ShieldCheck, SignalHigh, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import type { RiskDriver } from "@/api/types";

type RiskDriverListProps = {
  drivers?: RiskDriver[];
  protective?: RiskDriver[];
  limitations?: string[];
};

export function RiskDriverList({ drivers = [], protective = [], limitations = [] }: RiskDriverListProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <DriverColumn
        title="Main drivers"
        icon={<SignalHigh className="h-4 w-4 text-cyan-100" />}
        items={drivers.map((driver) => ({
          title: driver.factor?.replace(/_/g, " ") || "driver",
          detail: driver.interpretation || driver.component || "Component raised the score."
        }))}
      />
      <DriverColumn
        title="Protective factors"
        icon={<ShieldCheck className="h-4 w-4 text-emerald-100" />}
        items={protective.map((driver) => ({
          title: driver.factor?.replace(/_/g, " ") || "protective factor",
          detail: driver.interpretation || "This signal dampens priority."
        }))}
      />
      <DriverColumn
        title="Data limitations"
        icon={<TriangleAlert className="h-4 w-4 text-amber-100" />}
        items={limitations.map((limitation) => ({ title: limitation, detail: "Interpret with caution." }))}
      />
    </div>
  );
}

function DriverColumn({
  title,
  icon,
  items
}: {
  title: string;
  icon: ReactNode;
  items: Array<{ title: string; detail: string }>;
}) {
  return (
    <div className="rounded-lg border border-cyan-300/12 bg-slate-950/42 p-4">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      {items.length ? (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={`${title}-${item.title}`} className="border-l border-cyan-300/25 pl-3">
              <p className="text-sm capitalize text-slate-100">{item.title}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">{item.detail}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500">No dominant signal reported.</p>
      )}
    </div>
  );
}
