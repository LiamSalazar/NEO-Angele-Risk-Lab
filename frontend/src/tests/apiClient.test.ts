import { describe, expect, it } from "vitest";

import { buildApiUrl } from "@/api/client";
import { endpoints } from "@/api/endpoints";

describe("api client", () => {
  it("builds correct URLs", () => {
    expect(buildApiUrl("/health", "http://api.test/")).toBe("http://api.test/health");
    expect(buildApiUrl(endpoints.objects.detail("A 001"), "http://api.test")).toBe(
      "http://api.test/objects/A%20001"
    );
  });
});
