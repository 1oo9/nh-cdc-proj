import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CartView } from "./CartView";
import { writeCart } from "@/lib/cart";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("CartView", () => {
  beforeEach(() => {
    push.mockReset();
    window.sessionStorage.clear();
    writeCart("tok", [
      {
        productId: "p1",
        name: "Chicken Burger",
        quantity: 1,
        optionIds: [],
        optionNames: [],
        unitPriceCents: 1250,
      },
    ]);
  });

  it("posts order then navigates to confirmation", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "order-1", number: 1 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<CartView token="tok" />);

    expect(await screen.findByText(/Chicken Burger/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Valider la commande/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringMatching(/\/orders$/),
        expect.objectContaining({ method: "POST" }),
      );
    });
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.table_token).toBe("tok");
    expect(body.idempotency_key).toBeTruthy();
    expect(body.items[0].product_id).toBe("p1");
    expect(push).toHaveBeenCalledWith("/t/tok/confirmation/order-1");
  });
});
