import { Outlet } from "react-router-dom";

import { ErrorState } from "@/components/common/ErrorState";
import { OrbitalBackdrop } from "@/components/mission/OrbitalBackdrop";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { useApiHealth, useSystemStatus } from "@/hooks/useApiHealth";

export function AppShell() {
  const health = useApiHealth();
  const status = useSystemStatus();
  const readiness = status.data?.details?.risk?.risk_scores_available
    ? "risk-ready"
    : status.data?.details?.gold_features_available
      ? "features-ready"
      : "not-ready";

  return (
    <div className="min-h-screen">
      <OrbitalBackdrop />
      <Sidebar />
      <div className="lg:pl-72">
        <Topbar
          apiStatus={health.isError ? "unavailable" : health.data?.status}
          readiness={readiness}
          lastUpdate={health.data?.timestamp_utc}
        />
        <main className="mx-auto w-full max-w-[1680px] px-4 py-6 lg:px-8 lg:py-8">
          {health.isError ? (
            <ErrorState
              className="mb-6"
              title="Backend unavailable"
              error={health.error}
              endpoint="/health"
              onRetry={() => {
                health.refetch();
                status.refetch();
              }}
            />
          ) : null}
          <Outlet />
        </main>
      </div>
    </div>
  );
}
