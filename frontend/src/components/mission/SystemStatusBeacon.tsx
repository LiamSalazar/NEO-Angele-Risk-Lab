import { cn } from "@/lib/utils";

type BeaconState = "online" | "partial" | "missing data" | "insufficient data" | "unavailable";

type SystemStatusBeaconProps = {
  state?: BeaconState | string;
  label?: string;
  compact?: boolean;
};

const stateStyles: Record<string, string> = {
  online: "bg-emerald-300 shadow-[0_0_24px_rgba(143,240,193,0.45)]",
  partial: "bg-amber-300 shadow-[0_0_24px_rgba(247,199,95,0.4)]",
  "missing data": "bg-orange-300 shadow-[0_0_24px_rgba(255,154,92,0.4)]",
  "insufficient data": "bg-amber-300 shadow-[0_0_24px_rgba(247,199,95,0.4)]",
  unavailable: "bg-rose-400 shadow-[0_0_24px_rgba(255,93,115,0.44)]"
};

const normalize = (state?: string): BeaconState => {
  const normalized = String(state || "unavailable").replace(/_/g, " ").toLowerCase();
  if (normalized === "ok" || normalized === "success") return "online";
  if (normalized === "strong" || normalized === "usable") return "online";
  if (normalized === "minimal") return "partial";
  if (normalized === "not ready") return "missing data";
  if (normalized === "partial success" || normalized === "partial") return "partial";
  if (normalized === "missing data") return "missing data";
  if (normalized === "insufficient data" || normalized === "skipped missing dependency") {
    return "insufficient data";
  }
  return normalized in stateStyles ? (normalized as BeaconState) : "unavailable";
};

export function SystemStatusBeacon({
  state = "unavailable",
  label = "API",
  compact
}: SystemStatusBeaconProps) {
  const normalized = normalize(state);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-cyan-300/15 bg-slate-950/55 px-3 py-1 text-xs text-slate-300",
        compact && "px-2"
      )}
    >
      <span className="relative flex h-2.5 w-2.5">
        <span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-50 animate-beacon",
            stateStyles[normalized]
          )}
        />
        <span className={cn("relative inline-flex h-2.5 w-2.5 rounded-full", stateStyles[normalized])} />
      </span>
      {!compact ? (
        <>
          {label}: <span className="font-mono text-slate-100">{normalized}</span>
        </>
      ) : null}
    </span>
  );
}
