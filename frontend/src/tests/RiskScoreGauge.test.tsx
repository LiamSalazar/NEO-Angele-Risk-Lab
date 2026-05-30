import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "@/components/common/EmptyState";
import { GNNStatusPanel } from "@/components/gnn/GNNStatusPanel";
import { RiskCategoryBadge } from "@/components/risk/RiskCategoryBadge";
import { RiskScoreGauge } from "@/components/risk/RiskScoreGauge";
import { SimulationSummary } from "@/components/simulation/SimulationSummary";

describe("Risk components", () => {
  it("RiskScoreGauge renders category and score", () => {
    render(<RiskScoreGauge score={72.4} category="high" />);

    expect(screen.getByTestId("risk-score-value")).toHaveTextContent("72.4");
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("RiskCategoryBadge maps categories", () => {
    render(<RiskCategoryBadge category="critical" />);

    expect(screen.getByTestId("risk-category-badge")).toHaveTextContent("Critical");
  });

  it("GNN status panel handles skipped_missing_dependency", () => {
    render(<GNNStatusPanel status="ok" result={{ torch_geometric_available: false }} />);

    expect(screen.getByText("skipped_missing_dependency")).toBeInTheDocument();
  });

  it("EmptyState shows command suggestion", () => {
    render(<EmptyState title="No data" command="python -m neo_ange.cli risk build" />);

    expect(screen.getByText("python -m neo_ange.cli risk build")).toBeInTheDocument();
  });

  it("Simulation summary renders p95 and category shift adjacent metrics", () => {
    render(
      <SimulationSummary
        result={{
          object_key: "A-001",
          base_score: 45,
          mean_score: 47,
          std_score: 2.1,
          p95_score: 55,
          probability_score_above_60: 0.08,
          probability_score_above_80: 0,
          p95_category: "elevated"
        }}
      />
    );

    expect(screen.getByTestId("simulation-summary")).toHaveTextContent("55.0");
    expect(screen.getByText("Elevated")).toBeInTheDocument();
  });
});
