import {
  Activity,
  BarChart3,
  GitBranch,
  Home,
  Lightbulb,
  Orbit,
  Radar,
  ScrollText
} from "lucide-react";

export const APP_NAME = "Neo Angele Risk Lab";

export const NAV_ITEMS = [
  { label: "Control Panel", path: "/", icon: Home },
  { label: "Risk Ranking", path: "/ranking", icon: BarChart3 },
  { label: "Object Profile", path: "/objects", icon: Radar },
  { label: "Score Simulation", path: "/monte-carlo", icon: Activity },
  { label: "Orbital Simulation", path: "/orbital-simulation", icon: Orbit },
  { label: "Orbital Graph", path: "/gnn", icon: GitBranch },
  { label: "Findings", path: "/findings", icon: Lightbulb },
  { label: "Methodology", path: "/methodology", icon: ScrollText }
] as const;

export const RISK_COMPONENTS = [
  { key: "physical_risk_component", label: "Physical" },
  { key: "orbital_risk_component", label: "Orbital" },
  { key: "approach_risk_component", label: "Approach" },
  { key: "sentry_risk_component", label: "Sentry" },
  { key: "uncertainty_risk_component", label: "Uncertainty" },
  { key: "data_quality_component", label: "Data quality" }
] as const;

export const RISK_CATEGORIES = ["low", "moderate", "elevated", "high", "critical"] as const;

export const ENTITY_NAMES = [
  "Asteroid",
  "AsteroidIdentity",
  "Orbit",
  "PhysicalProperties",
  "CloseApproachSummary",
  "SentryRiskSignal",
  "RiskScore",
  "MonteCarloResult",
  "OrbitalGraph"
] as const;
