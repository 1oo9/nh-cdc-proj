import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AdminLoginForm } from "./AdminLoginForm";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("AdminLoginForm", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("stores token after successful login", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ access_token: "test-token", token_type: "bearer" }),
      }),
    );

    render(<AdminLoginForm />);
    await user.click(screen.getByRole("button", { name: "Connexion" }));

    expect(window.localStorage.getItem("nh_admin_token")).toBe("test-token");
  });

  it("shows error when login fails", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
      }),
    );

    render(<AdminLoginForm />);
    await user.click(screen.getByRole("button", { name: "Connexion" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Identifiants invalides");
  });
});
