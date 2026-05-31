type QueryValue = string | number | boolean | null | undefined;

export const withQuery = (path: string, params?: Record<string, QueryValue>) => {
  const search = new URLSearchParams();

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    search.set(key, String(value));
  });

  const query = search.toString();
  return query ? `${path}?${query}` : path;
};

export const endpoints = {
  health: "/health",
  status: "/status",
  objects: {
    list: (params?: {
      limit?: number;
      offset?: number;
      category?: string;
      sentry_flag?: boolean;
    }) => withQuery("/objects", params),
    detail: (objectKey: string) => `/objects/${encodeURIComponent(objectKey)}`
  },
  domain: {
    object: (objectKey: string) => `/domain/objects/${encodeURIComponent(objectKey)}`
  },
  rankings: {
    top: (limit = 20) => withQuery("/rankings/top", { limit }),
    summary: "/rankings/summary",
    category: (category: string, limit = 20) =>
      withQuery(`/rankings/category/${encodeURIComponent(category)}`, { limit })
  },
  risk: {
    build: "/risk/build",
    status: "/risk/status",
    explain: (objectKey: string) => `/risk/explain/${encodeURIComponent(objectKey)}`,
    methodology: "/risk/methodology"
  },
  simulations: {
    object: "/simulations/object",
    batch: "/simulations/batch",
    status: "/simulations/status",
    latestForObject: (objectKey: string) =>
      `/simulations/object/${encodeURIComponent(objectKey)}/latest`
  },
  orbitalSimulation: {
    object: "/orbital-simulation/object",
    batch: "/orbital-simulation/batch",
    status: "/orbital-simulation/status",
    latestForObject: (objectKey: string) =>
      `/orbital-simulation/object/${encodeURIComponent(objectKey)}/latest`,
    findings: "/orbital-simulation/findings"
  },
  findings: {
    summary: "/findings/summary",
    risk: "/findings/risk",
    scoreSimulation: "/findings/score-simulation",
    orbitalSimulation: "/findings/orbital-simulation",
    orbitalGraph: "/findings/orbital-graph",
    modelEvidence: "/findings/model-evidence",
    object: (objectKey: string) => `/findings/object/${encodeURIComponent(objectKey)}`
  },
  modelEvidence: {
    summary: "/model-evidence/summary",
    cards: "/model-evidence/cards",
    predictions: withQuery("/model-evidence/predictions", { mode: "full" }),
    disagreements: "/model-evidence/disagreements",
    object: (objectKey: string) => `/model-evidence/object/${encodeURIComponent(objectKey)}`
  },
  gnn: {
    status: "/gnn/status",
    buildGraph: "/gnn/build-graph",
    run: "/gnn/run",
    summary: "/gnn/summary",
    graph: (limitNodes = 220) => withQuery("/gnn/graph", { limit_nodes: limitNodes }),
    metrics: "/gnn/metrics",
    neighbors: (objectKey: string) => `/gnn/object/${encodeURIComponent(objectKey)}/neighbors`
  }
} as const;
