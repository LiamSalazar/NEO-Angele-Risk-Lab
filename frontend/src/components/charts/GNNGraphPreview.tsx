import ReactECharts from "echarts-for-react";
import { useMemo } from "react";

import type { GNNGraphEdge, GNNGraphNode } from "@/api/types";
import { EmptyState } from "@/components/common/EmptyState";
import { baseChartOptions } from "@/lib/charts";
import { objectKey } from "@/lib/formatters";
import { riskTone, scoreToCategory } from "@/lib/risk";

type GNNGraphPreviewProps = {
  nodes?: GNNGraphNode[];
  edges?: GNNGraphEdge[];
  height?: number;
  limit?: number;
};

export function GNNGraphPreview({ nodes = [], edges = [], height = 420, limit = 180 }: GNNGraphPreviewProps) {
  const limitedNodes = nodes.slice(0, limit);
  const nodeIds = new Set(limitedNodes.map((node) => Number(node.node_id)));
  const limitedEdges = edges.filter((edge) => nodeIds.has(Number(edge.source)) && nodeIds.has(Number(edge.target)));

  const option = useMemo(
    () => ({
      ...baseChartOptions,
      tooltip: {
        ...baseChartOptions.tooltip,
        formatter: (params: { data?: Record<string, unknown> }) => {
          const data = params.data ?? {};
          return `${data.name ?? "node"}<br/>score: ${data.score ?? "n/a"}<br/>category: ${data.category ?? "n/a"}`;
        }
      },
      series: [
        {
          type: "graph",
          layout: "force",
          roam: true,
          draggable: true,
          force: {
            repulsion: 76,
            edgeLength: 54,
            gravity: 0.08
          },
          lineStyle: {
            color: "rgba(148,197,211,0.22)",
            width: 1
          },
          data: limitedNodes.map((node) => {
            const score = Number(node.risk_score_0_100 ?? 0);
            const category = String(node.risk_category || scoreToCategory(score));
            return {
              id: String(node.node_id),
              name: objectKey(node) || String(node.node_id),
              score: Number.isFinite(score) ? score.toFixed(1) : "n/a",
              category,
              symbolSize: Math.max(8, Math.min(34, 8 + score / 3.5)),
              itemStyle: { color: riskTone(category).hex }
            };
          }),
          links: limitedEdges.map((edge) => ({
            source: String(edge.source),
            target: String(edge.target),
            value: edge.similarity ?? edge.distance
          })),
          emphasis: {
            focus: "adjacency",
            lineStyle: { width: 2, color: "#42f2ff" }
          }
        }
      ]
    }),
    [limitedEdges, limitedNodes]
  );

  if (limitedNodes.length === 0) {
    return (
      <EmptyState
        title="Orbital graph unavailable"
        description="Graph nodes are missing or the graph has not been exported."
        command="python -m neo_ange.cli gnn build-graph --k 10 --min-nodes 100"
      />
    );
  }

  return <ReactECharts option={option} style={{ height, width: "100%" }} />;
}
