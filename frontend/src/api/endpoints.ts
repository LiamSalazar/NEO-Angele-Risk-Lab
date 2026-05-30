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
