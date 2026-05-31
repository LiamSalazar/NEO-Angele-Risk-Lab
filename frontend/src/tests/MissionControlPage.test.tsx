import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { MissionControlPage } from "@/pages/MissionControlPage";
import { mockApiResponse } from "@/tests/setup";

function renderMissionControl() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MissionControlPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("MissionControlPage", () => {
  it("handles health success", async () => {
    renderMissionControl();

    expect(await screen.findByText("Control Panel")).toBeInTheDocument();
    expect(await screen.findByText(/Analytical observatory/i)).toBeInTheDocument();
    expect(await screen.findByText("Risk Overview")).toBeInTheDocument();
  });

  it("handles backend unavailable", async () => {
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (new URL(url).pathname === "/health") {
        throw new Error("connection refused");
      }
      return new Response(JSON.stringify(mockApiResponse(url)), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    });

    renderMissionControl();

    expect(await screen.findByText("Control Panel")).toBeInTheDocument();
    expect(await screen.findByText("Risk Overview")).toBeInTheDocument();
  });
});
