import { RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { SystemStatusBeacon } from "@/components/mission/SystemStatusBeacon";
import { Button } from "@/components/ui/button";
import { APP_NAME } from "@/lib/constants";
import { formatTimestamp } from "@/lib/formatters";

type TopbarProps = {
  apiStatus?: string;
  readiness?: string;
  lastUpdate?: string | null;
};

export function Topbar({ apiStatus = "unavailable", readiness = "unknown", lastUpdate }: TopbarProps) {
  const queryClient = useQueryClient();

  return (
    <header className="sticky top-0 z-20 border-b border-cyan-300/12 bg-[#040914]/78 backdrop-blur-xl">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 lg:px-8">
        <div className="min-w-0 lg:hidden">
          <p className="technical-label text-[10px] text-cyan-100">Mission observatory</p>
          <h1 className="truncate font-semibold text-white">{APP_NAME}</h1>
        </div>
        <div className="hidden min-w-0 lg:block">
          <p className="technical-label text-[10px] text-slate-500">FastAPI bridge</p>
          <p className="mt-1 font-mono text-xs text-slate-300">VITE_API_BASE_URL connected console</p>
        </div>
        <div className="flex items-center gap-2">
          <SystemStatusBeacon state={apiStatus} label="API" />
          <span className="hidden rounded-full border border-cyan-300/15 bg-slate-950/50 px-3 py-1 text-xs text-slate-300 md:inline-flex">
            readiness: <span className="ml-1 font-mono text-slate-100">{readiness}</span>
          </span>
          <span className="hidden rounded-full border border-cyan-300/15 bg-slate-950/50 px-3 py-1 text-xs text-slate-300 xl:inline-flex">
            update: <span className="ml-1 font-mono text-slate-100">{formatTimestamp(lastUpdate)}</span>
          </span>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            title="Refresh telemetry"
            onClick={() => queryClient.invalidateQueries()}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
