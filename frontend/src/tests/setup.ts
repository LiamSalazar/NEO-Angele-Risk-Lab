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

const finding = {
  title: "Current dataset is analyzable",
  short_text: "The active dataset contains 1 object with one PHA label.",
  technical_basis: "Counts are computed from the active mocked risk-score table.",
  related_objects: ["A-001"],
  importance: "high",
  source_module: "dataset"
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

  if (path === "/findings/summary") {
    return {
      status: "success",
      details: {
        summary: {
          finding_count: 1,
          dataset_rows: 1,
          risk_rows: 1,
          score_simulation_rows: 0,
          orbital_simulation_rows: 1,
          graph_nodes: 0,
          graph_edges: 0
        },
        findings: [finding]
      }
    };
  }

  if (
    [
      "/findings/risk",
      "/findings/score-simulation",
      "/findings/orbital-simulation",
      "/findings/orbital-graph",
      "/findings/model-evidence"
    ].includes(path)
  ) {
    return { status: "success", details: { findings: [finding] } };
  }

  if (path === "/model-evidence/summary") {
    return {
      status: "success",
      details: {
        best_defensible_model: {
          model_name: "random_forest",
          model_family: "tabular",
          feature_set: "orbital_only",
          target: "pha",
          selection_metric: 0.82,
          leakage_risk: "low",
          recommended_use: "secondary evidence",
          metrics: {
            accuracy: 0.86,
            f1: 0.71,
            pr_auc: 0.83,
            precision: 0.8,
            recall: 0.64,
            false_negative_rate: 0.36
          }
        },
        best_defensible_model_interpretation:
          "random_forest on orbital_only provides secondary evidence for pattern consistency.",
        main_evidence_conclusion:
          "random_forest on orbital_only provides secondary evidence for pattern consistency.",
        prediction_count: 1,
        prediction_rows_eval: 1,
        unique_eval_object_keys: 1,
        prediction_rows_full: 1,
        unique_full_object_keys: 1,
        total_gold_objects: 1,
        total_risk_objects: 1,
        coverage_ratio: 1,
        disagreement_count: 0,
        recommended_use: "secondary evidence",
        ranking_source: "Risk Priority Score"
      }
    };
  }

  if (path === "/model-evidence/predictions") {
    return {
      status: "success",
      details: {
        mode: "full",
        predictions: [
          {
            object_key: "A-001",
            model_name: "random_forest",
            feature_set: "orbital_only",
            predicted_probability: 0.8,
            confidence_bucket: "medium",
            leakage_risk: "low",
            evidence_role: "secondary_evidence"
          }
        ]
      }
    };
  }

  if (path === "/model-evidence/object/A-001") {
    return {
      status: "success",
      details: {
        object_key: "A-001",
        predictions: [
          {
            object_key: "A-001",
            model_name: "random_forest",
            feature_set: "orbital_only",
            predicted_probability: 0.8,
            confidence_bucket: "medium"
          }
        ],
        disagreements: []
      }
    };
  }

  if (path === "/orbital-simulation/status") {
    return {
      status: "ok",
      details: {
        source_rows_available: true,
        orbital_simulation_available: true,
        row_count: 1,
        latest_manifest_status: "success"
      }
    };
  }

  if (path.includes("/orbital-simulation/object/")) {
    return {
      status: "success",
      result: {
        object_key: "A-001",
        n_clones: 20,
        horizon_days: 365,
        time_step_days: 30,
        simulated_min_distance_p05_au: 0.02,
        simulated_min_distance_p50_au: 0.05,
        simulated_min_distance_p95_au: 0.12,
        dispersion_index: 0.4,
        scenario_category: "variable",
        interpretation: "Mock orbital scenario.",
        distance_trace: { day: [0, 30], p05: [0.03, 0.02], p50: [0.06, 0.05], p95: [0.14, 0.12] }
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
