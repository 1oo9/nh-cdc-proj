import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KITCHEN_POLL_MS, KitchenBoard } from "./KitchenBoard";

const router = { push: vi.fn(), replace: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

class MockWebSocket {
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  close = vi.fn();
  constructor(_url: string) {
    MockWebSocket.instances.push(this);
  }
  static instances: MockWebSocket[] = [];
  static reset() {
    MockWebSocket.instances = [];
  }
}

const emptyTicketResponse = {
  ok: true,
  json: async () => [] as unknown[],
};

const ticketResponse = {
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
};

describe("KitchenBoard", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem("nh_kitchen_token", "kitchen-token");
    MockWebSocket.reset();
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("shows ticket table and lines then advances status on click", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(ticketResponse)
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
      })
      .mockResolvedValue(emptyTicketResponse);
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

  it("reloads tickets on poll interval and on websocket message", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn().mockResolvedValue(ticketResponse);
    vi.stubGlobal("fetch", fetchMock);

    render(<KitchenBoard />);
    await vi.advanceTimersByTimeAsync(0);
    expect(fetchMock.mock.calls.length).toBeGreaterThan(0);
    const afterMount = fetchMock.mock.calls.length;

    await vi.advanceTimersByTimeAsync(KITCHEN_POLL_MS);
    expect(fetchMock.mock.calls.length).toBeGreaterThan(afterMount);

    const beforeWs = fetchMock.mock.calls.length;
    expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    MockWebSocket.instances[0].onmessage?.({
      data: JSON.stringify({ type: "order_created", order_id: "x" }),
    });
    await vi.advanceTimersByTimeAsync(0);
    expect(fetchMock.mock.calls.length).toBeGreaterThan(beforeWs);
  });
});
