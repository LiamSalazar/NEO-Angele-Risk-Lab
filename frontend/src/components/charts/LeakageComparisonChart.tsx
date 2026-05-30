import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";

type LeakageComparisonChartProps = {
  rows?: Array<Record<string, unknown>>;
  height?: number;
};

const featureSets = [
  "full_features",
  "definition_features_only",
  "no_definition_features",
  "orbital_only",
  "approach_and_quality",
  "sentry_related"
];

export function LeakageComparisonChart({ rows, height = 260 }: LeakageComparisonChartProps) {
  const hasData = featureSets.some((name) =>
    Number.isFinite(Number((rows ?? []).find((row) => row.feature_set_name === name)?.f1))
  );

  const option = useMemo(
    () => {
      const lookup = new Map((rows ?? []).map((row) => [String(row.feature_set_name), row]));
      return {
        ...baseChartOptions,
        tooltip: { ...baseChartOptions.tooltip, trigger: "axis" },
        xAxis: {
          type: "category",
          data: featureSets,
          axisLabel: { color: "#9fb0c4", rotate: 24 },
          axisLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
        },
        yAxis: {
          type: "value",
          max: 1,
          axisLabel: { color: "#9fb0c4" },
          splitLine: { lineStyle: { color: "rgba(148,197,211,0.12)" } }
        },
        series: [
          {
            name: "f1",
            type: "bar",
            data: featureSets.map((name) => Number(lookup.get(name)?.f1 ?? 0)),
            itemStyle: { color: "#f7c75f", borderRadius: [5, 5, 0, 0] }
          }
        ]
      };
    },
    [rows]
  );

  if (!hasData) {
    return (
      <EmptyState
        title="Leakage comparison unavailable"
        description="Run baseline training and leakage audit to populate feature-set comparisons."
        command="python -m neo_ange.cli ml leakage-audit"
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
