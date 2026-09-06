"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { readCart, writeCart, type CartItem } from "@/lib/cart";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PublicMenu = {
  restaurant: { name: string; currency: string };
  table: { label: string; public_token: string };
  categories: Array<{
    id: string;
    name: string;
    products: Array<{
      id: string;
      name: string;
      description: string | null;
      price_cents: number;
      photo_url: string | null;
      options: Array<{
        id: string;
        name: string;
        price_delta_cents: number;
        group_name: string;
      }>;
    }>;
  }>;
};

type Props = { token: string };

export function PublicMenuView({ token }: Props) {
  const [menu, setMenu] = useState<PublicMenu | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cartCount, setCartCount] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetch(`${API_URL}/t/${token}/menu`)
      .then(async (response) => {
        if (!response.ok) {
          setError("Menu introuvable");
          return;
        }
        setMenu(await response.json());
      })
      .catch(() => setError("Menu introuvable"));
    setCartCount(readCart(token).reduce((n, item) => n + item.quantity, 0));
  }, [token]);

  function toggleOption(productId: string, optionId: string) {
    setSelectedOptions((prev) => {
      const current = prev[productId] ?? [];
      const next = current.includes(optionId)
        ? current.filter((id) => id !== optionId)
        : [...current, optionId];
      return { ...prev, [productId]: next };
    });
  }

  function addToCart(product: PublicMenu["categories"][0]["products"][0]) {
    const optionIds = selectedOptions[product.id] ?? [];
    const chosen = product.options.filter((option) => optionIds.includes(option.id));
    const unitPriceCents =
      product.price_cents + chosen.reduce((sum, option) => sum + option.price_delta_cents, 0);
    const items = readCart(token);
    const line: CartItem = {
      productId: product.id,
      name: product.name,
      quantity: 1,
      optionIds,
      optionNames: chosen.map((option) => option.name),
      unitPriceCents,
    };
    const existingIndex = items.findIndex(
      (item) =>
        item.productId === line.productId &&
        item.optionIds.slice().sort().join() === line.optionIds.slice().sort().join(),
    );
    if (existingIndex >= 0) {
      items[existingIndex] = {
        ...items[existingIndex],
        quantity: items[existingIndex].quantity + 1,
      };
    } else {
      items.push(line);
    }
    writeCart(token, items);
    setCartCount(items.reduce((n, item) => n + item.quantity, 0));
  }

  if (error) {
    return <p role="alert">{error}</p>;
  }
  if (!menu) {
    return <p>Chargement…</p>;
  }

  return (
    <div className="mx-auto max-w-lg space-y-8 p-4 pb-24">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{menu.restaurant.name}</h1>
          <p className="text-sm text-zinc-600">Table {menu.table.label}</p>
        </div>
        <Link
          href={`/t/${token}/panier`}
          className="rounded bg-zinc-900 px-3 py-2 text-sm text-white"
        >
          Panier ({cartCount})
        </Link>
      </header>
      {menu.categories.map((category) => (
        <section key={category.id}>
          <h2 className="mb-3 text-lg font-medium">{category.name}</h2>
          <ul className="space-y-4">
            {category.products.map((product) => (
              <li key={product.id} className="border-b border-zinc-200 pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{product.name}</p>
                    {product.description ? (
                      <p className="text-sm text-zinc-600">{product.description}</p>
                    ) : null}
                    {product.options.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-sm">
                        {product.options.map((option) => (
                          <li key={option.id}>
                            <label className="flex items-center gap-2">
                              <input
                                type="checkbox"
                                checked={(selectedOptions[product.id] ?? []).includes(option.id)}
                                onChange={() => toggleOption(product.id, option.id)}
                              />
                              {option.name}
                              {option.price_delta_cents
                                ? ` (+${(option.price_delta_cents / 100).toFixed(2)} €)`
                                : ""}
                            </label>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    <button
                      type="button"
                      className="mt-2 text-sm underline"
                      onClick={() => addToCart(product)}
                    >
                      Ajouter
                    </button>
                  </div>
                  <p className="shrink-0 font-medium">
                    {(product.price_cents / 100).toFixed(2)} €
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
