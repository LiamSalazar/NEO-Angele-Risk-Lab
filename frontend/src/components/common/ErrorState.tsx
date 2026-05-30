import { AlertTriangle } from "lucide-react";

import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ErrorStateProps = {
  title?: string;
  error?: unknown;
  endpoint?: string;
  onRetry?: () => void;
  className?: string;
};

export function ErrorState({
  title = "Telemetry link unavailable",
  error,
  endpoint,
  onRetry,
  className
}: ErrorStateProps) {
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "The backend did not return a usable response.";

  return (
    <div className={cn("console-panel rounded-lg border-rose-300/25 p-5", className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-md border border-rose-300/25 bg-rose-300/10 text-rose-100">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-white">{title}</h3>
          <p className="mt-1 text-sm text-slate-300">{message}</p>
          {endpoint ? (
            <p className="mt-2 font-mono text-xs text-slate-500">endpoint: {endpoint}</p>
          ) : null}
        </div>
        {onRetry ? (
          <Button type="button" variant="danger" onClick={onRetry}>
            Reconnect
          </Button>
        ) : null}
      </div>
    </div>
  );
}
