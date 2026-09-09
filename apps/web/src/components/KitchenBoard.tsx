"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Poll fallback when WebSocket is down (S6). */
export const KITCHEN_POLL_MS = 5000;

type Ticket = {
  id: string;
  number: number;
  status: string;
  table_label: string;
  total_cents: number;
  items: Array<{
    product_name: string;
    quantity: number;
    unit_price_cents: number;
    options: string[];
  }>;
};

const STATUS_LABEL: Record<string, string> = {
  nouvelle: "nouvelle",
  acceptee: "acceptée",
  en_preparation: "en préparation",
  prete: "prête",
  terminee: "terminée",
};

const NEXT_STATUS: Record<string, { value: string; label: string } | null> = {
  nouvelle: { value: "acceptee", label: "acceptée" },
  acceptee: { value: "en_preparation", label: "en préparation" },
  en_preparation: { value: "prete", label: "prête" },
  prete: { value: "terminee", label: "terminée" },
  terminee: null,
};

function wsUrl(token: string) {
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/kitchen/ws?token=${encodeURIComponent(token)}`;
}

export function KitchenBoard() {
  const router = useRouter();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = window.localStorage.getItem("nh_kitchen_token");
    if (!token) {
      router.replace("/cuisine/login");
      return;
    }
    setError(null);
    const response = await fetch(`${API_URL}/kitchen/orders`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.status === 401) {
      window.localStorage.removeItem("nh_kitchen_token");
      router.replace("/cuisine/login");
      return;
    }
    if (!response.ok) {
      setError("Impossible de charger les commandes");
      return;
    }
    const data: unknown = await response.json();
    setTickets(Array.isArray(data) ? (data as Ticket[]) : []);
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const id = window.setInterval(() => {
      void load();
    }, KITCHEN_POLL_MS);
    return () => window.clearInterval(id);
  }, [load]);

  useEffect(() => {
    const token = window.localStorage.getItem("nh_kitchen_token");
    if (!token) return;

    let closed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;

    function connect() {
      if (closed) return;
      socket = new WebSocket(wsUrl(token!));
      socket.onmessage = () => {
        void load();
      };
      socket.onclose = () => {
        if (closed) return;
        reconnectTimer = window.setTimeout(connect, 2000);
      };
    }

    connect();
    return () => {
      closed = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [load]);

  async function advance(ticket: Ticket) {
    const next = NEXT_STATUS[ticket.status];
    if (!next) return;
    const token = window.localStorage.getItem("nh_kitchen_token");
    if (!token) return;
    const response = await fetch(`${API_URL}/kitchen/orders/${ticket.id}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status: next.value }),
    });
    if (!response.ok) {
      setError("Statut non mis à jour");
      return;
    }
    const updated = (await response.json()) as Ticket;
    if (updated.status === "terminee") {
      setTickets((prev) => prev.filter((t) => t.id !== updated.id));
    } else {
      setTickets((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4">
      <header className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Cuisine</h1>
        <button
          type="button"
          className="rounded border border-zinc-300 px-3 py-2 text-sm"
          onClick={() => void load()}
        >
          Rafraîchir
        </button>
      </header>
      {error ? <p role="alert">{error}</p> : null}
      {tickets.length === 0 ? (
        <p>Aucune commande ouverte.</p>
      ) : (
        <ul className="space-y-4">
          {tickets.map((ticket) => {
            const next = NEXT_STATUS[ticket.status];
            return (
              <li
                key={ticket.id}
                className="border border-zinc-200 bg-white p-4 shadow-sm"
              >
                <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                  <p className="text-lg font-semibold">
                    #{ticket.number} — Table {ticket.table_label}
                  </p>
                  <p className="text-sm text-zinc-600">
                    {STATUS_LABEL[ticket.status] ?? ticket.status}
                  </p>
                </div>
                <ul className="mb-3 space-y-1 text-sm">
                  {ticket.items.map((item, index) => (
                    <li key={`${item.product_name}-${index}`}>
                      {item.quantity} × {item.product_name}
                      {item.options.length > 0
                        ? ` (${item.options.join(", ")})`
                        : ""}
                    </li>
                  ))}
                </ul>
                <p className="mb-3 font-medium">
                  {(ticket.total_cents / 100).toFixed(2)} €
                </p>
                {next ? (
                  <button
                    type="button"
                    className="bg-zinc-900 px-4 py-2 text-sm text-white"
                    onClick={() => void advance(ticket)}
                  >
                    {next.label}
                  </button>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
