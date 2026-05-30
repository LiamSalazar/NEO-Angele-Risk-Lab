import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";

type ModelComparisonChartProps = {
  metrics?: Array<Record<string, unknown>>;
  height?: number;
};

const metricNames = ["precision", "recall", "f1", "pr_auc", "roc_auc", "false_negative_rate"];

export function ModelComparisonChart({ metrics, height = 280 }: ModelComparisonChartProps) {
  const rows = (metrics ?? []).filter((row) => row && typeof row === "object");
  const hasData = rows.some((row) => metricNames.some((metric) => Number.isFinite(Number(row[metric]))));

  const option = useMemo(
    () => ({
      ...baseChartOptions,
      tooltip: { ...baseChartOptions.tooltip, trigger: "axis" },
      legend: { textStyle: { color: "#9fb0c4" }, top: 0 },
      xAxis: {
        type: "category",
        data: rows.map((row, index) => String(row.feature_set_name || row.model_name || `run ${index + 1}`)),
        axisLabel: { color: "#9fb0c4", rotate: 18 },
        axisLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      yAxis: {
        type: "value",
        max: 1,
        axisLabel: { color: "#9fb0c4" },
        splitLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
      },
      series: ["f1", "pr_auc", "roc_auc"].map((metric, index) => ({
        name: metric,
        type: "bar",
        data: rows.map((row) => Number(row[metric] ?? 0)),
        itemStyle: { color: ["#42f2ff", "#8ff0c1", "#f7c75f"][index] }
      }))
    }),
    [rows]
  );

  if (!hasData) {
    return (
      <EmptyState
        title="Baseline metrics unavailable"
        description="No completed ML baseline metrics were exposed through status manifests."
        command="python -m neo_ange.cli ml run-all"
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
