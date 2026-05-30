import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "@/App";

describe("App", () => {
  it("renders the observatory shell", async () => {
    render(<App />);

    expect(await screen.findAllByText("Neo Angele Risk Lab")).not.toHaveLength(0);
    expect(await screen.findByText(/Near-Earth Object risk intelligence/i)).toBeInTheDocument();
  });
});
