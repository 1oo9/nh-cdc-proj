"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATUS_LABEL: Record<string, string> = {
  nouvelle: "nouvelle",
  acceptee: "acceptée",
  en_preparation: "en préparation",
  prete: "prête",
  terminee: "terminée",
};

type Order = {
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

type Props = { token: string; orderId: string };

export function ConfirmationView({ token, orderId }: Props) {
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/orders/${orderId}`)
      .then(async (response) => {
        if (!response.ok) {
          setError("Commande introuvable");
          return;
        }
        setOrder(await response.json());
      })
      .catch(() => setError("Commande introuvable"));
  }, [orderId]);

  if (error) {
    return (
      <div className="mx-auto max-w-lg p-4">
        <p role="alert" className="rounded border border-red-200 bg-red-50 px-3 py-2">
          {error}
        </p>
      </div>
    );
  }
  if (!order) return <p className="p-4">Chargement…</p>;

  return (
    <div className="mx-auto max-w-lg space-y-6 p-4">
      <h1 className="text-2xl font-semibold">Commande confirmée</h1>
      <p>
        Commande #{order.number} — Table {order.table_label}
      </p>
      <p className="text-sm text-zinc-600">
        Statut : {STATUS_LABEL[order.status] ?? order.status}
      </p>
      <ul className="space-y-2">
        {order.items.map((item, index) => (
          <li key={`${item.product_name}-${index}`}>
            {item.quantity} × {item.product_name}
            {item.options.length ? ` (${item.options.join(", ")})` : ""}
          </li>
        ))}
      </ul>
      <p className="font-semibold">Total {(order.total_cents / 100).toFixed(2)} €</p>
      <Link href={`/t/${token}`} className="inline-block min-h-11 underline">
        Retour au menu
      </Link>
    </div>
  );
}
