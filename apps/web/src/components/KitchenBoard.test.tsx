import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { KitchenBoard } from "./KitchenBoard";

const router = { push: vi.fn(), replace: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

describe("KitchenBoard", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem("nh_kitchen_token", "kitchen-token");
  });

  it("shows ticket table and lines then advances status on click", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: "o1",
            number: 1,
            status: "nouvelle",
            table_label: "14",
            total_cents: 1350,
            items: [
              {
                product_name: "Chicken Burger",
                quantity: 1,
                unit_price_cents: 1350,
                options: ["fromage"],
              },
            ],
          },
        ],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "o1",
          number: 1,
          status: "acceptee",
          table_label: "14",
          total_cents: 1350,
          items: [
            {
              product_name: "Chicken Burger",
              quantity: 1,
              unit_price_cents: 1350,
              options: ["fromage"],
            },
          ],
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    render(<KitchenBoard />);

    expect(await screen.findByText(/#1/)).toBeInTheDocument();
    expect(screen.getByText(/Table 14/)).toBeInTheDocument();
    expect(screen.getByText(/Chicken Burger/)).toBeInTheDocument();
    expect(screen.getByText(/fromage/)).toBeInTheDocument();
    expect(screen.getByText(/nouvelle/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /acceptée/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringMatching(/\/kitchen\/orders\/o1$/),
        expect.objectContaining({ method: "PATCH" }),
      );
    });
    expect(await screen.findByText(/acceptée/i)).toBeInTheDocument();
  });
});
