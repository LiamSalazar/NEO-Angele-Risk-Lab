import "@testing-library/jest-dom/vitest";
import React from "react";
import { beforeEach, vi } from "vitest";

const object = {
  object_key: "A-001",
  des: "2026 QA",
  full_name: "2026 QA",
  risk_score_0_100: 48.5,
  risk_category: "elevated",
  physical_risk_component: 0.32,
  orbital_risk_component: 0.62,
  approach_risk_component: 0.41,
  sentry_risk_component: 0.18,
  uncertainty_risk_component: 0.55,
  data_quality_component: 0.21,
  sentry_flag: false,
  pha: true,
  moid: 0.023,
  h: 19.2
};

export const mockApiResponse = (url: string) => {
  const path = new URL(url).pathname;

  if (path === "/health") {
    return {
      status: "ok",
      service: "neo-ange-risk-lab-api",
      version: "0.1.0",
      timestamp_utc: "2026-05-29T10:00:00Z"
    };
  }

  if (path === "/status") {
    return {
      status: "ok",
      details: {
        bronze_available: true,
        silver_available: true,
        gold_features_available: true,
        risk_scores_available: true,
        simulation_reports_available: false,
        latest_manifest_paths: { ml: ["reports/manifests/ml/latest.json"] },
        latest_manifests: { ml: { status: "insufficient_data", metrics_summary: {} } },
        risk: { row_count: 1, risk_scores_available: true, latest_reports: [] },
        simulation: { row_count: 0, latest_manifest_status: null, latest_reports: [] }
      }
    };
  }

  if (path === "/rankings/summary") {
    return {
      status: "success",
      details: {
        n_objects: 1,
        score_mean: 48.5,
        score_median: 48.5,
        score_max: 48.5,
        category_counts: { elevated: 1 }
      }
    };
  }

  if (path === "/rankings/top" || path === "/objects") {
    return { status: "success", objects: [object] };
  }

  if (path === "/gnn/status") {
    return {
      status: "ok",
      result: {
        graph_exists: false,
        node_count: 0,
        edge_count: 0,
        risk_scores_count: 1,
        torch_geometric_available: false,
        dataset_readiness: {
          status: "minimal",
          counts: { risk_scores_count: 1 },
          readiness: { ml_baseline: "not_ready", gnn: "not_ready", frontend: "minimal" },
          pha_distribution: { true: 1, false: 0, unknown: 0 },
          recommended_next_command: "python -m neo_ange.cli risk build"
        },
        latest_reports: []
      }
    };
  }

  if (path === "/simulations/status") {
    return { status: "ok", row_count: 0, latest_manifest_status: null };
  }

  if (path === "/risk/methodology") {
    return { status: "success", details: { content: "Risk methodology content." } };
  }

  if (path.includes("/simulations/object/")) {
    return { status: "not_found", result: null, message: "Simulation results not found." };
  }

  return { status: "missing_data", objects: [], result: null, details: {} };
};

vi.mock("echarts-for-react", () => ({
  default: () => React.createElement("div", { "data-testid": "echart" })
}));

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    return new Response(JSON.stringify(mockApiResponse(url)), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  });
});
