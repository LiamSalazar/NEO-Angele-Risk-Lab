import type { EChartsOption } from "echarts";

export const chartText = "#d8e5f2";
export const chartMuted = "#8090a3";
export const chartGrid = "rgba(148, 197, 211, 0.12)";

export const baseChartOptions: EChartsOption = {
  backgroundColor: "transparent",
  textStyle: {
    color: chartText,
    fontFamily: "Inter, system-ui, sans-serif"
  },
  tooltip: {
    trigger: "item",
    backgroundColor: "rgba(5, 13, 25, 0.92)",
    borderColor: "rgba(66, 242, 255, 0.24)",
    textStyle: { color: chartText }
  },
  grid: {
    left: 28,
    right: 18,
    top: 28,
    bottom: 28,
    containLabel: true
  }
};

export const axisStyle = {
  axisLine: { lineStyle: { color: chartGrid } },
  axisLabel: { color: chartMuted },
  splitLine: { lineStyle: { color: chartGrid } }
};
