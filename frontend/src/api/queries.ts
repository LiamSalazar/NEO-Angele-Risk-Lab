import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "./client";
import { endpoints } from "./endpoints";
import type {
  ExplanationResponse,
  GNNGraphResult,
  GNNMetricsResult,
  GNNResponse,
  GNNStatusResult,
  HealthResponse,
  NeighborResult,
  OrbitalSimulationResult,
  RankingResponse,
  RiskObjectResponse,
  SimulationResponse,
  StatusResponse,
  SystemStatusDetails
} from "./types";

export const queryKeys = {
  health: ["health"] as const,
  status: ["status"] as const,
  objects: (params?: unknown) => ["objects", params] as const,
  object: (objectKey?: string) => ["object", objectKey] as const,
  domainObject: (objectKey?: string) => ["domain-object", objectKey] as const,
  rankingTop: (limit: number) => ["ranking-top", limit] as const,
  rankingSummary: ["ranking-summary"] as const,
  riskStatus: ["risk-status"] as const,
  riskExplanation: (objectKey?: string) => ["risk-explanation", objectKey] as const,
  riskMethodology: ["risk-methodology"] as const,
  simulationStatus: ["simulation-status"] as const,
  simulationLatest: (objectKey?: string) => ["simulation-latest", objectKey] as const,
  orbitalSimulationStatus: ["orbital-simulation-status"] as const,
  orbitalSimulationLatest: (objectKey?: string) =>
    ["orbital-simulation-latest", objectKey] as const,
  findingsSummary: ["findings-summary"] as const,
  findingsGroup: (group: string) => ["findings-group", group] as const,
  modelEvidenceSummary: ["model-evidence-summary"] as const,
  modelEvidenceCards: ["model-evidence-cards"] as const,
  modelEvidencePredictions: ["model-evidence-predictions"] as const,
  modelEvidenceDisagreements: ["model-evidence-disagreements"] as const,
  modelEvidenceObject: (objectKey?: string) => ["model-evidence-object", objectKey] as const,
  gnnStatus: ["gnn-status"] as const,
  gnnSummary: ["gnn-summary"] as const,
  gnnGraph: (limit: number) => ["gnn-graph", limit] as const,
  gnnMetrics: ["gnn-metrics"] as const,
  gnnNeighbors: (objectKey?: string) => ["gnn-neighbors", objectKey] as const
};

const standardQuery = {
  retry: 1,
  staleTime: 45_000
};

export function useHealthQuery() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.get<HealthResponse>(endpoints.health),
    ...standardQuery
  });
}

export function useSystemStatusQuery() {
  return useQuery({
    queryKey: queryKeys.status,
    queryFn: () => apiClient.get<StatusResponse<SystemStatusDetails>>(endpoints.status),
    ...standardQuery
  });
}

export function useObjectsQuery(params?: {
  limit?: number;
  offset?: number;
  category?: string;
  sentry_flag?: boolean;
}) {
  return useQuery({
    queryKey: queryKeys.objects(params),
    queryFn: () => apiClient.get<RankingResponse>(endpoints.objects.list(params)),
    ...standardQuery
  });
}

export function useObjectQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.object(objectKey),
    queryFn: () => apiClient.get<RiskObjectResponse>(endpoints.objects.detail(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useDomainObjectQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.domainObject(objectKey),
    queryFn: () => apiClient.get<RiskObjectResponse>(endpoints.domain.object(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useRankingTopQuery(limit = 20) {
  return useQuery({
    queryKey: queryKeys.rankingTop(limit),
    queryFn: () => apiClient.get<RankingResponse>(endpoints.rankings.top(limit)),
    ...standardQuery
  });
}

export function useRankingSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.rankingSummary,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.rankings.summary),
    ...standardQuery
  });
}

export function useRiskStatusQuery() {
  return useQuery({
    queryKey: queryKeys.riskStatus,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.risk.status),
    ...standardQuery
  });
}

export function useRiskExplanationQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.riskExplanation(objectKey),
    queryFn: () => apiClient.get<ExplanationResponse>(endpoints.risk.explain(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useRiskMethodologyQuery() {
  return useQuery({
    queryKey: queryKeys.riskMethodology,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.risk.methodology),
    ...standardQuery,
    staleTime: 5 * 60_000
  });
}

export function useBuildRiskMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<StatusResponse>(endpoints.risk.build),
    onSuccess: () => queryClient.invalidateQueries()
  });
}

export function useSimulationStatusQuery() {
  return useQuery({
    queryKey: queryKeys.simulationStatus,
    queryFn: () => apiClient.get<StatusResponse | Record<string, unknown>>(endpoints.simulations.status),
    ...standardQuery
  });
}

export function useLatestSimulationQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.simulationLatest(objectKey),
    queryFn: () =>
      apiClient.get<SimulationResponse>(endpoints.simulations.latestForObject(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useSimulateObjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { object_key: string; n_simulations: number; random_state?: number | null }) =>
      apiClient.post<SimulationResponse>(endpoints.simulations.object, body, { timeoutMs: 60_000 }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.simulationLatest(variables.object_key) });
    }
  });
}

export function useSimulateBatchMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { limit: number; n_simulations: number; random_state?: number | null }) =>
      apiClient.post<SimulationResponse>(endpoints.simulations.batch, body, { timeoutMs: 120_000 }),
    onSuccess: () => queryClient.invalidateQueries()
  });
}

export function useOrbitalSimulationStatusQuery() {
  return useQuery({
    queryKey: queryKeys.orbitalSimulationStatus,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.orbitalSimulation.status),
    ...standardQuery
  });
}

export function useLatestOrbitalSimulationQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.orbitalSimulationLatest(objectKey),
    queryFn: () =>
      apiClient.get<SimulationResponse & { result?: OrbitalSimulationResult | null }>(
        endpoints.orbitalSimulation.latestForObject(objectKey ?? "")
      ),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useRunOrbitalSimulationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      object_key: string;
      n_clones: number;
      horizon_days: number;
      time_step_days: number;
      random_state?: number | null;
    }) =>
      apiClient.post<SimulationResponse>(
        endpoints.orbitalSimulation.object,
        body,
        { timeoutMs: 120_000 }
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.orbitalSimulationStatus });
      queryClient.invalidateQueries({
        queryKey: queryKeys.orbitalSimulationLatest(variables.object_key)
      });
    }
  });
}

export function useRunOrbitalBatchMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      limit: number;
      n_clones: number;
      horizon_days: number;
      time_step_days: number;
      random_state?: number | null;
    }) =>
      apiClient.post<SimulationResponse>(
        endpoints.orbitalSimulation.batch,
        body,
        { timeoutMs: 180_000 }
      ),
    onSuccess: () => queryClient.invalidateQueries()
  });
}

export function useFindingsSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.findingsSummary,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.findings.summary),
    ...standardQuery
  });
}

export function useFindingsGroupQuery(group: keyof typeof endpoints.findings) {
  return useQuery({
    queryKey: queryKeys.findingsGroup(group),
    queryFn: () => {
      const endpoint = endpoints.findings[group];
      return apiClient.get<StatusResponse>(typeof endpoint === "string" ? endpoint : endpoints.findings.summary);
    },
    ...standardQuery
  });
}

export function useModelEvidenceSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.modelEvidenceSummary,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.modelEvidence.summary),
    ...standardQuery
  });
}

export function useModelEvidenceCardsQuery() {
  return useQuery({
    queryKey: queryKeys.modelEvidenceCards,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.modelEvidence.cards),
    ...standardQuery
  });
}

export function useModelEvidencePredictionsQuery() {
  return useQuery({
    queryKey: queryKeys.modelEvidencePredictions,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.modelEvidence.predictions),
    ...standardQuery
  });
}

export function useModelEvidenceDisagreementsQuery() {
  return useQuery({
    queryKey: queryKeys.modelEvidenceDisagreements,
    queryFn: () => apiClient.get<StatusResponse>(endpoints.modelEvidence.disagreements),
    ...standardQuery
  });
}

export function useModelEvidenceObjectQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.modelEvidenceObject(objectKey),
    queryFn: () => apiClient.get<StatusResponse>(endpoints.modelEvidence.object(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}

export function useGNNStatusQuery() {
  return useQuery({
    queryKey: queryKeys.gnnStatus,
    queryFn: () => apiClient.get<GNNResponse<GNNStatusResult>>(endpoints.gnn.status),
    ...standardQuery
  });
}

export function useBuildGNNGraphMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { k: number; min_nodes: number }) =>
      apiClient.post<GNNResponse>(endpoints.gnn.buildGraph, body, { timeoutMs: 120_000 }),
    onSuccess: () => queryClient.invalidateQueries()
  });
}

export function useRunGNNMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { target: string; k: number; min_nodes: number }) =>
      apiClient.post<GNNResponse>(endpoints.gnn.run, body, { timeoutMs: 180_000 }),
    onSuccess: () => queryClient.invalidateQueries()
  });
}

export function useGNNSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.gnnSummary,
    queryFn: () => apiClient.get<GNNResponse>(endpoints.gnn.summary),
    ...standardQuery
  });
}

export function useGNNGraphQuery(limitNodes = 220) {
  return useQuery({
    queryKey: queryKeys.gnnGraph(limitNodes),
    queryFn: () => apiClient.get<GNNResponse<GNNGraphResult>>(endpoints.gnn.graph(limitNodes)),
    ...standardQuery
  });
}

export function useGNNMetricsQuery() {
  return useQuery({
    queryKey: queryKeys.gnnMetrics,
    queryFn: () => apiClient.get<GNNResponse<GNNMetricsResult>>(endpoints.gnn.metrics),
    ...standardQuery
  });
}

export function useGNNNeighborsQuery(objectKey?: string) {
  return useQuery({
    queryKey: queryKeys.gnnNeighbors(objectKey),
    queryFn: () => apiClient.get<GNNResponse<NeighborResult>>(endpoints.gnn.neighbors(objectKey ?? "")),
    enabled: Boolean(objectKey),
    ...standardQuery
  });
}
