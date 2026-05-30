import {
  Activity,
  Atom,
  BarChart3,
  BrainCircuit,
  GitBranch,
  Home,
  Radar,
  ScrollText,
  ServerCog
} from "lucide-react";

export const APP_NAME = "Neo Angele Risk Lab";

export const NAV_ITEMS = [
  { label: "Mission Control", path: "/", icon: Home },
  { label: "Risk Ranking", path: "/ranking", icon: BarChart3 },
  { label: "Asteroid Profile", path: "/objects", icon: Radar },
  { label: "Monte Carlo Lab", path: "/monte-carlo", icon: Activity },
  { label: "ML & Leakage Lab", path: "/ml-lab", icon: BrainCircuit },
  { label: "GNN Research Lab", path: "/gnn", icon: GitBranch },
  { label: "Domain Explorer", path: "/domain", icon: Atom },
  { label: "Pipeline Monitor", path: "/pipeline", icon: ServerCog },
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
