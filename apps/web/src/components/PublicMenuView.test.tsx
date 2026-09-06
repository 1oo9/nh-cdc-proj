import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PublicMenuView } from "./PublicMenuView";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("PublicMenuView", () => {
  it("shows restaurant name and available product from menu API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          restaurant: { name: "Chicken Street Paris", currency: "EUR" },
          table: { label: "14", public_token: "abc" },
          categories: [
            {
              id: "c1",
              name: "Burgers",
              products: [
                {
                  id: "p1",
                  name: "Chicken Burger",
                  description: "Classic",
                  price_cents: 1250,
                  photo_url: null,
                  options: [
                    {
                      id: "o1",
                      name: "fromage",
                      price_delta_cents: 100,
                      group_name: "Suppléments",
                    },
                  ],
                },
              ],
            },
          ],
        }),
      }),
    );

    render(<PublicMenuView token="abc" />);

    expect(await screen.findByText("Chicken Street Paris")).toBeInTheDocument();
    expect(screen.getByText("Table 14")).toBeInTheDocument();
    expect(screen.getByText("Chicken Burger")).toBeInTheDocument();
    expect(screen.getByText("12.50 €")).toBeInTheDocument();
  });
});
