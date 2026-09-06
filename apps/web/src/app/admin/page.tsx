"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Restaurant = {
  id: string;
  name: string;
  slug: string;
};

export default function AdminHomePage() {
  const router = useRouter();
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = window.localStorage.getItem("nh_admin_token");
    if (!token) {
      router.replace("/admin/login");
      return;
    }
    fetch(`${API_URL}/admin/restaurants`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (response.status === 401) {
          router.replace("/admin/login");
          return;
        }
        if (!response.ok) {
          setError("Impossible de charger les restaurants");
          return;
        }
        setRestaurants(await response.json());
      })
      .catch(() => setError("Impossible de charger les restaurants"));
  }, [router]);

  return (
    <main className="mx-auto min-h-screen max-w-3xl p-8">
      <h1 className="mb-2 text-2xl font-semibold">Restaurants</h1>
      <p className="mb-6 text-sm text-zinc-600">Gestion interne du menu</p>
      {error ? <p role="alert">{error}</p> : null}
      <ul className="space-y-3">
        {restaurants.map((restaurant) => (
          <li key={restaurant.id}>
            <Link
              className="block border border-zinc-200 px-4 py-3 hover:bg-zinc-50"
              href={`/admin/restaurants/${restaurant.id}`}
            >
              {restaurant.name}
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
