"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Category = { id: string; name: string; sort_order: number; active: boolean };
type Product = {
  id: string;
  name: string;
  price_cents: number;
  available: boolean;
  sort_order: number;
  category_id: string;
  photo_url: string | null;
};

function authHeaders(): HeadersInit {
  const token = window.localStorage.getItem("nh_admin_token");
  return {
    Authorization: `Bearer ${token ?? ""}`,
    "Content-Type": "application/json",
  };
}

export default function RestaurantAdminPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [tables, setTables] = useState<Array<{ id: string; label: string; public_token: string }>>([]);
  const [categoryName, setCategoryName] = useState("");
  const [productName, setProductName] = useState("");
  const [tableLabel, setTableLabel] = useState("");
  const [priceCents, setPriceCents] = useState("1250");
  const [categoryId, setCategoryId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = window.localStorage.getItem("nh_admin_token");
    if (!token) {
      router.replace("/admin/login");
      return;
    }
    const [catsRes, productsRes, tablesRes] = await Promise.all([
      fetch(`${API_URL}/admin/restaurants/${id}/categories`, { headers: authHeaders() }),
      fetch(`${API_URL}/admin/restaurants/${id}/products`, { headers: authHeaders() }),
      fetch(`${API_URL}/admin/restaurants/${id}/tables`, { headers: authHeaders() }),
    ]);
    if (catsRes.status === 401 || productsRes.status === 401 || tablesRes.status === 401) {
      router.replace("/admin/login");
      return;
    }
    setCategories(await catsRes.json());
    setProducts(await productsRes.json());
    setTables(await tablesRes.json());
  }, [id, router]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!categoryId && categories.length > 0) {
      setCategoryId(categories[0].id);
    }
  }, [categories, categoryId]);

  async function createCategory(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API_URL}/admin/restaurants/${id}/categories`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        name: categoryName,
        sort_order: categories.length + 1,
        active: true,
      }),
    });
    if (!response.ok) {
      setMessage("Échec création catégorie");
      return;
    }
    setCategoryName("");
    setMessage("Catégorie créée");
    await load();
  }

  async function createProduct(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API_URL}/admin/restaurants/${id}/products`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({
        category_id: categoryId,
        name: productName,
        price_cents: Number(priceCents),
        available: true,
        sort_order: products.length + 1,
      }),
    });
    if (!response.ok) {
      setMessage("Échec création produit");
      return;
    }
    setProductName("");
    setMessage("Produit créé");
    await load();
  }

  async function toggleAvailability(product: Product) {
    await fetch(`${API_URL}/admin/products/${product.id}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ available: !product.available }),
    });
    await load();
  }

  async function createTable(event: FormEvent) {
    event.preventDefault();
    const response = await fetch(`${API_URL}/admin/restaurants/${id}/tables`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ label: tableLabel }),
    });
    if (!response.ok) {
      setMessage("Échec création table");
      return;
    }
    setTableLabel("");
    setMessage("Table créée");
    await load();
  }

  async function downloadQr(tableId: string, label: string) {
    const response = await fetch(`${API_URL}/admin/tables/${tableId}/qr.png`, {
      headers: authHeaders(),
    });
    if (!response.ok) {
      setMessage("Échec téléchargement QR");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `table-${label}-qr.png`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto min-h-screen max-w-3xl space-y-8 p-8">
      <h1 className="text-2xl font-semibold">Menu</h1>
      {message ? <p>{message}</p> : null}

      <section>
        <h2 className="mb-3 text-lg font-medium">Catégories</h2>
        <ul className="mb-4 space-y-1 text-sm">
          {categories.map((category) => (
            <li key={category.id}>
              {category.sort_order}. {category.name}
            </li>
          ))}
        </ul>
        <form onSubmit={createCategory} className="flex gap-2">
          <input
            className="flex-1 border border-zinc-300 px-3 py-2"
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
            placeholder="Nouvelle catégorie"
            required
          />
          <button type="submit" className="bg-zinc-900 px-3 py-2 text-white">
            Ajouter
          </button>
        </form>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">Tables & QR</h2>
        <ul className="mb-4 space-y-2 text-sm">
          {tables.map((table) => (
            <li key={table.id} className="flex items-center justify-between border border-zinc-200 px-3 py-2">
              <span>
                Table {table.label}
                <span className="ml-2 text-zinc-500">/t/{table.public_token}</span>
              </span>
              <button
                type="button"
                className="underline"
                onClick={() => void downloadQr(table.id, table.label)}
              >
                QR PNG
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={createTable} className="flex gap-2">
          <input
            className="flex-1 border border-zinc-300 px-3 py-2"
            value={tableLabel}
            onChange={(e) => setTableLabel(e.target.value)}
            placeholder="Libellé table (ex. 14)"
            required
          />
          <button type="submit" className="bg-zinc-900 px-3 py-2 text-white">
            Ajouter table
          </button>
        </form>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">Produits</h2>
        <ul className="mb-4 space-y-2 text-sm">
          {products.map((product) => (
            <li key={product.id} className="flex items-center justify-between border border-zinc-200 px-3 py-2">
              <span>
                {product.name} — {(product.price_cents / 100).toFixed(2)} €
                {product.available ? "" : " (indisponible)"}
              </span>
              <button
                type="button"
                className="text-sm underline"
                onClick={() => void toggleAvailability(product)}
              >
                {product.available ? "Rendre indisponible" : "Rendre disponible"}
              </button>
            </li>
          ))}
        </ul>
        <form onSubmit={createProduct} className="grid gap-2">
          <select
            className="border border-zinc-300 px-3 py-2"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            required
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <input
            className="border border-zinc-300 px-3 py-2"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="Nom du produit"
            required
          />
          <input
            className="border border-zinc-300 px-3 py-2"
            value={priceCents}
            onChange={(e) => setPriceCents(e.target.value)}
            placeholder="Prix en centimes"
            required
          />
          <button type="submit" className="bg-zinc-900 px-3 py-2 text-white">
            Ajouter produit
          </button>
        </form>
      </section>
    </main>
  );
}
