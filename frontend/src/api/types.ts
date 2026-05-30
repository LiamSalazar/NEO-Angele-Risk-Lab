export type ApiStatus =
  | "ok"
  | "success"
  | "partial"
  | "partial_success"
  | "missing_data"
  | "insufficient_data"
  | "skipped_missing_dependency"
  | "not_found"
  | "failed"
  | "error"
  | string;

export type RiskCategory = "low" | "moderate" | "elevated" | "high" | "critical" | string;

export type ApiRecord = Record<string, unknown>;

export interface HealthResponse {
  status: ApiStatus;
  service: string;
  version: string;
  timestamp_utc: string;
}

export interface StatusResponse<T = ApiRecord> {
  status: ApiStatus;
  details: T;
  message?: string | null;
}

export interface RankingResponse {
  status: ApiStatus;
  objects: RiskObject[];
  summary?: RankingSummary | null;
  message?: string | null;
}

export interface RiskObjectResponse {
  status: ApiStatus;
  object: RiskObject | null;
  message?: string | null;
}

export interface ExplanationResponse {
  status: ApiStatus;
  explanation: RiskExplanation | null;
  message?: string | null;
}

export interface SimulationResponse {
  status: ApiStatus;
  result?: SimulationResult | null;
  results?: SimulationResult[];
  summary?: ApiRecord | null;
  message?: string | null;
}

export interface GNNResponse<T = ApiRecord> {
  status: ApiStatus;
  result?: T | null;
  message?: string | null;
}

export interface SystemStatusDetails {
  bronze_available?: boolean;
  silver_available?: boolean;
  gold_features_available?: boolean;
  risk_scores_available?: boolean;
  simulation_reports_available?: boolean;
  latest_manifest_paths?: Record<string, string[]>;
  latest_manifests?: Record<string, ApiRecord | null>;
  risk?: RiskPipelineStatus;
  simulation?: SimulationPipelineStatus;
  [key: string]: unknown;
}

export interface RiskPipelineStatus {
  status?: ApiStatus;
  gold_features_available?: boolean;
  risk_scores_available?: boolean;
  risk_scores_path?: string;
  row_count?: number;
  latest_reports?: string[];
  latest_manifests?: string[];
  latest_manifest_status?: ApiStatus | null;
  score_version?: string;
  [key: string]: unknown;
}

export interface SimulationPipelineStatus {
  status?: ApiStatus;
  risk_scores_available?: boolean;
  simulation_results_available?: boolean;
  simulation_results_path?: string;
  row_count?: number;
  latest_reports?: string[];
  latest_manifests?: string[];
  latest_manifest_status?: ApiStatus | null;
  simulation_version?: string;
  [key: string]: unknown;
}

export interface DatasetReadiness {
  status?: string;
  counts?: Record<string, number>;
  readiness?: Record<string, string>;
  pha_distribution?: { true: number; false: number; unknown: number };
  sentry_coverage?: CoverageSummary;
  cad_coverage?: CoverageSummary;
  recommended_next_command?: string;
  outputs?: Record<string, string>;
  [key: string]: unknown;
}

export interface CoverageSummary {
  covered_rows?: number;
  total_rows?: number;
  coverage_ratio?: number;
  columns?: string[];
}

export interface RankingSummary {
  n_objects?: number;
  score_min?: number | null;
  score_mean?: number | null;
  score_median?: number | null;
  score_max?: number | null;
  category_counts?: Record<string, number>;
  top_object?: RiskObject | null;
  [key: string]: unknown;
}

export interface RiskObject extends ApiRecord {
  object_key?: string;
  spkid?: string | number;
  des?: string;
  name?: string;
  full_name?: string;
  risk_score_0_100?: number;
  risk_score?: number;
  risk_category?: RiskCategory;
  risk_explanation_short?: string;
  physical_risk_component?: number;
  orbital_risk_component?: number;
  approach_risk_component?: number;
  sentry_risk_component?: number;
  uncertainty_risk_component?: number;
  data_quality_component?: number;
  sentry_flag?: boolean | string | number;
  pha?: boolean | string | number;
  neo?: boolean | string | number;
}

export interface RiskDriver {
  factor: string;
  component?: string;
  value?: number;
  interpretation?: string;
}

export interface RiskExplanation {
  status?: ApiStatus;
  object_key?: string;
  risk_score_0_100?: number;
  risk_category?: RiskCategory;
  main_drivers?: RiskDriver[];
  protective_factors?: RiskDriver[];
  data_limitations?: string[];
  short_explanation?: string;
  technical_explanation?: string;
  [key: string]: unknown;
}

export interface SimulationResult extends ApiRecord {
  object_key?: string;
  n_simulations?: number;
  base_score?: number;
  mean_score?: number;
  std_score?: number;
  min_score?: number;
  p05_score?: number;
  median_score?: number;
  p95_score?: number;
  max_score?: number;
  probability_score_above_60?: number;
  probability_score_above_80?: number;
  category_shift_probability?: number;
  base_category?: RiskCategory;
  p95_category?: RiskCategory;
  simulated_at_utc?: string;
}

export interface GNNStatusResult {
  dataset_readiness?: DatasetReadiness;
  risk_scores_count?: number;
  graph_exists?: boolean;
  node_count?: number;
  edge_count?: number;
  latest_reports?: string[];
  torch_geometric_available?: boolean;
  status?: ApiStatus;
  [key: string]: unknown;
}

export interface GNNGraphNode extends ApiRecord {
  node_id?: number;
  object_key?: string;
  risk_score_0_100?: number;
  risk_category?: RiskCategory;
  pha?: boolean | string | number;
}

export interface GNNGraphEdge extends ApiRecord {
  source?: number;
  target?: number;
  similarity?: number;
  distance?: number;
}

export interface GNNGraphResult {
  nodes?: GNNGraphNode[];
  edges?: GNNGraphEdge[];
  graph_summary?: ApiRecord;
}

export interface GNNMetricsResult {
  metrics?: ApiRecord[];
}

export interface NeighborResult {
  object_key?: string;
  neighbors?: ApiRecord[];
}
