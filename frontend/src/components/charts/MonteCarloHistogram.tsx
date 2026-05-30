import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import type { SimulationResult } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";
import { scoreColor } from "@/lib/risk";

type MonteCarloHistogramProps = {
  result?: SimulationResult | null;
  height?: number;
};

export function MonteCarloHistogram({ result, height = 280 }: MonteCarloHistogramProps) {
  const quantiles = [
    { label: "p05", value: result?.p05_score },
    { label: "median", value: result?.median_score },
    { label: "p95", value: result?.p95_score }
  ].filter((item) => Number.isFinite(Number(item.value)));

  const option = useMemo(
    () => ({
      ...baseChartOptions,
      tooltip: { ...baseChartOptions.tooltip, trigger: "axis" },
      xAxis: {
        type: "category",
        data: quantiles.map((item) => item.label),
        axisLabel: { color: "#9fb0c4" },
        axisLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 100,
        axisLabel: { color: "#9fb0c4" },
        splitLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      series: [
        {
          name: "score quantile",
          type: "bar",
          barWidth: 28,
          data: quantiles.map((item) => ({
            value: item.value,
            itemStyle: {
              color: scoreColor(Number(item.value), result?.p95_category),
              borderRadius: [5, 5, 0, 0]
            }
          })),
          markLine: {
            symbol: "none",
            lineStyle: { color: "#42f2ff", type: "dashed" },
            data: Number.isFinite(Number(result?.base_score))
              ? [{ yAxis: result?.base_score, name: "base score" }]
              : []
          }
        }
      ]
    }),
    [quantiles, result?.base_score, result?.p95_category]
  );

  if (!result || quantiles.length === 0) {
    return (
      <EmptyState
        title="Simulation distribution unavailable"
        description="Run an object simulation or load latest results."
        command="python -m neo_ange.cli simulate batch --limit 50 --n-simulations 500"
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
