import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "@/App";

describe("App", () => {
  it("renders the observatory shell", async () => {
    render(<App />);

    expect(await screen.findAllByText("Neo Angele Risk Lab")).not.toHaveLength(0);
    expect(await screen.findByText("Control Panel")).toBeInTheDocument();
    expect(screen.queryByText("Domain Explorer")).not.toBeInTheDocument();
    expect(screen.queryByText("Pipeline Monitor")).not.toBeInTheDocument();
  });
});
