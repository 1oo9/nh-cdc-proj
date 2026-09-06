"use client";

import { useEffect, useState } from "react";

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
      options: Array<{ name: string; price_delta_cents: number; group_name: string }>;
    }>;
  }>;
};

type Props = { token: string };

export function PublicMenuView({ token }: Props) {
  const [menu, setMenu] = useState<PublicMenu | null>(null);
  const [error, setError] = useState<string | null>(null);

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
  }, [token]);

  if (error) {
    return <p role="alert">{error}</p>;
  }
  if (!menu) {
    return <p>Chargement…</p>;
  }

  return (
    <div className="mx-auto max-w-lg space-y-8 p-4">
      <header>
        <h1 className="text-2xl font-semibold">{menu.restaurant.name}</h1>
        <p className="text-sm text-zinc-600">Table {menu.table.label}</p>
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
                      <ul className="mt-1 text-sm text-zinc-500">
                        {product.options.map((option) => (
                          <li key={`${option.group_name}-${option.name}`}>
                            {option.name}
                            {option.price_delta_cents
                              ? ` (+${(option.price_delta_cents / 100).toFixed(2)} €)`
                              : ""}
                          </li>
                        ))}
                      </ul>
                    ) : null}
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
