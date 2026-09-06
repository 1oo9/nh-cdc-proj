"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  cartTotalCents,
  clearCart,
  readCart,
  writeCart,
  type CartItem,
} from "@/lib/cart";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Props = { token: string };

export function CartView({ token }: Props) {
  const router = useRouter();
  const [items, setItems] = useState<CartItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const total = useMemo(() => cartTotalCents(items), [items]);

  useEffect(() => {
    setItems(readCart(token));
  }, [token]);

  function persist(next: CartItem[]) {
    writeCart(token, next);
    setItems(next);
  }

  async function submitOrder() {
    setError(null);
    setSubmitting(true);
    const idempotencyKey =
      window.sessionStorage.getItem(`nh_idem_${token}`) ?? crypto.randomUUID();
    window.sessionStorage.setItem(`nh_idem_${token}`, idempotencyKey);
    try {
      const response = await fetch(`${API_URL}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          table_token: token,
          idempotency_key: idempotencyKey,
          items: items.map((item) => ({
            product_id: item.productId,
            quantity: item.quantity,
            option_ids: item.optionIds,
          })),
        }),
      });
      if (!response.ok) {
        setError(
          response.status === 409
            ? "Un produit n’est plus disponible"
            : "Commande impossible",
        );
        setSubmitting(false);
        return;
      }
      const order = (await response.json()) as { id: string };
      clearCart(token);
      window.sessionStorage.removeItem(`nh_idem_${token}`);
      router.push(`/t/${token}/confirmation/${order.id}`);
    } catch {
      setError("Commande impossible");
      setSubmitting(false);
    }
  }

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-lg space-y-4 p-4">
        <h1 className="text-2xl font-semibold">Panier</h1>
        <p>Votre panier est vide.</p>
        <Link href={`/t/${token}`} className="underline">
          Retour au menu
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg space-y-6 p-4">
      <h1 className="text-2xl font-semibold">Panier</h1>
      <ul className="space-y-3">
        {items.map((item, index) => (
          <li key={`${item.productId}-${index}`} className="border-b border-zinc-200 pb-3">
            <div className="flex justify-between gap-3">
              <div>
                <p className="font-medium">
                  {item.quantity} × {item.name}
                </p>
                {item.optionNames.length > 0 ? (
                  <p className="text-sm text-zinc-600">{item.optionNames.join(", ")}</p>
                ) : null}
              </div>
              <p>{((item.unitPriceCents * item.quantity) / 100).toFixed(2)} €</p>
            </div>
            <button
              type="button"
              className="mt-1 text-sm underline"
              onClick={() => persist(items.filter((_, i) => i !== index))}
            >
              Retirer
            </button>
          </li>
        ))}
      </ul>
      <p className="text-lg font-semibold">Total {(total / 100).toFixed(2)} €</p>
      {error ? <p role="alert">{error}</p> : null}
      <button
        type="button"
        disabled={submitting}
        className="w-full bg-zinc-900 px-4 py-3 text-white disabled:opacity-60"
        onClick={() => void submitOrder()}
      >
        Valider la commande
      </button>
      <Link href={`/t/${token}`} className="block text-sm underline">
        Continuer les achats
      </Link>
    </div>
  );
}
