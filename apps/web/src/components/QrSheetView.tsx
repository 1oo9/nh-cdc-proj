"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SheetTable = {
  id: string;
  label: string;
  public_token: string;
  menu_url: string;
  qr_png_base64: string;
};

type Sheet = {
  restaurant_name: string;
  tables: SheetTable[];
};

type Props = { restaurantId: string };

export function QrSheetView({ restaurantId }: Props) {
  const router = useRouter();
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = window.localStorage.getItem("nh_admin_token");
    if (!token) {
      router.replace("/admin/login");
      return;
    }
    fetch(`${API_URL}/admin/restaurants/${restaurantId}/qr-sheet`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (response.status === 401) {
          router.replace("/admin/login");
          return;
        }
        if (!response.ok) {
          setError("Impossible de charger la feuille QR");
          return;
        }
        setSheet(await response.json());
      })
      .catch(() => setError("Impossible de charger la feuille QR"));
  }, [restaurantId, router]);

  if (error) {
    return (
      <p role="alert" className="rounded border border-red-200 bg-red-50 px-3 py-2">
        {error}
      </p>
    );
  }
  if (!sheet) {
    return <p>Chargement…</p>;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 print:p-0">
      <header className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <div>
          <h1 className="text-2xl font-semibold">Feuille QR</h1>
          <p className="text-sm text-zinc-600">{sheet.restaurant_name}</p>
        </div>
        <button
          type="button"
          className="min-h-11 bg-zinc-900 px-4 py-2 text-white"
          onClick={() => window.print()}
        >
          Imprimer
        </button>
      </header>
      <p className="hidden text-center text-xl font-semibold print:block">
        {sheet.restaurant_name} — QR tables
      </p>
      <ul className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 print:grid-cols-3">
        {sheet.tables.map((table) => (
          <li
            key={table.id}
            className="flex flex-col items-center border border-zinc-300 bg-white p-4 text-center"
          >
            <img
              src={`data:image/png;base64,${table.qr_png_base64}`}
              alt={`QR table ${table.label}`}
              className="h-40 w-40"
            />
            <p className="mt-3 text-lg font-semibold">Table {table.label}</p>
            <p className="mt-1 text-xs text-zinc-500 break-all">{table.menu_url}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
