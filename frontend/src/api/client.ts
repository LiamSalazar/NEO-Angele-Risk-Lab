const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  endpoint: string;
  statusCode?: number;
  details?: unknown;

  constructor(message: string, endpoint: string, statusCode?: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.endpoint = endpoint;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return (envUrl || DEFAULT_API_BASE_URL).replace(/\/+$/, "");
};

export const buildApiUrl = (endpoint: string, baseUrl = getApiBaseUrl()) => {
  if (/^https?:\/\//i.test(endpoint)) {
    return endpoint;
  }
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${baseUrl.replace(/\/+$/, "")}${normalizedEndpoint}`;
};

type RequestOptions = {
  timeoutMs?: number;
};

async function request<T>(
  method: "GET" | "POST",
  endpoint: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  );

  try {
    const response = await fetch(buildApiUrl(endpoint), {
      method,
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" })
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal
    });

    const text = await response.text();
    const payload = text ? JSON.parse(text) : null;

    if (!response.ok) {
      throw new ApiError(
        payload?.message || `API request failed with status ${response.status}`,
        endpoint,
        response.status,
        payload
      );
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("API request timed out", endpoint);
    }

    throw new ApiError(error instanceof Error ? error.message : "Network request failed", endpoint);
  } finally {
    window.clearTimeout(timeout);
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>("GET", endpoint, undefined, options),
  post: <T, B = unknown>(endpoint: string, body?: B, options?: RequestOptions) =>
    request<T>("POST", endpoint, body, options)
};
