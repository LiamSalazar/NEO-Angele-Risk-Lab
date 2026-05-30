import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";
import { RISK_CATEGORIES } from "@/lib/constants";
import { riskTone } from "@/lib/risk";

type RiskDistributionChartProps = {
  categoryCounts?: Record<string, number> | null;
  height?: number;
};

export function RiskDistributionChart({ categoryCounts, height = 260 }: RiskDistributionChartProps) {
  const total = Object.values(categoryCounts ?? {}).reduce((sum, value) => sum + Number(value || 0), 0);

  const option = useMemo(
    () => ({
      ...baseChartOptions,
      tooltip: { ...baseChartOptions.tooltip, trigger: "axis" },
      xAxis: {
        type: "category",
        data: RISK_CATEGORIES,
        axisLabel: { color: "#9fb0c4" },
        axisLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      yAxis: {
        type: "value",
        axisLabel: { color: "#9fb0c4" },
        splitLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      series: [
        {
          type: "bar",
          barWidth: 22,
          data: RISK_CATEGORIES.map((category) => ({
            value: categoryCounts?.[category] ?? 0,
            itemStyle: {
              color: riskTone(category).hex,
              borderRadius: [5, 5, 0, 0]
            }
          }))
        }
      ]
    }),
    [categoryCounts]
  );

  if (!total) {
    return (
      <EmptyState
        title="Risk distribution unavailable"
        description="Risk scores are not available yet."
        command="python -m neo_ange.cli risk build"
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
