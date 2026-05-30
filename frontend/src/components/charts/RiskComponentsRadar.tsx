import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import type { RiskObject } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";
import { RISK_COMPONENTS } from "@/lib/constants";

type RiskComponentsRadarProps = {
  object?: RiskObject | null;
  height?: number;
};

export function RiskComponentsRadar({ object, height = 310 }: RiskComponentsRadarProps) {
  const values = RISK_COMPONENTS.map((component) => Number(object?.[component.key] ?? 0));
  const hasValues = values.some((value) => Number.isFinite(value) && value > 0);

  const option = useMemo(
    () => ({
      ...baseChartOptions,
      radar: {
        radius: "62%",
        center: ["50%", "52%"],
        axisName: { color: "#b8c7d8", fontSize: 11 },
        splitLine: { lineStyle: { color: "rgba(148,197,211,0.13)" } },
        splitArea: { areaStyle: { color: ["rgba(66,242,255,0.04)", "rgba(143,240,193,0.03)"] } },
        axisLine: { lineStyle: { color: "rgba(148,197,211,0.14)" } },
        indicator: RISK_COMPONENTS.map((component) => ({ name: component.label, max: 1 }))
      },
      series: [
        {
          type: "radar",
          data: [
            {
              value: values,
              name: "component intensity",
              areaStyle: { color: "rgba(66,242,255,0.16)" },
              lineStyle: { color: "#42f2ff", width: 2 },
              itemStyle: { color: "#8ff0c1" }
            }
          ]
        }
      ]
    }),
    [values]
  );

  if (!hasValues) {
    return (
      <EmptyState
        title="Component telemetry unavailable"
        description="This object does not have component-level score fields yet."
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
