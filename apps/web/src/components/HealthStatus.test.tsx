import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { HealthStatus } from "./HealthStatus";

describe("HealthStatus", () => {
  it("shows API ok when health returns ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => ({ status: "ok" }),
      }),
    );

    render(<HealthStatus />);

    expect(await screen.findByText("API ok")).toBeInTheDocument();
  });
});
