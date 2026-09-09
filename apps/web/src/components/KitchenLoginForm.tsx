"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function KitchenLoginForm() {
  const router = useRouter();
  const [slug, setSlug] = useState("chicken-street-paris");
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const response = await fetch(`${API_URL}/kitchen/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ restaurant_slug: slug, pin }),
    });
    if (!response.ok) {
      setError("PIN ou restaurant invalide");
      return;
    }
    const body = (await response.json()) as { access_token: string };
    window.localStorage.setItem("nh_kitchen_token", body.access_token);
    router.push("/cuisine");
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto flex w-full max-w-sm flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Restaurant
        <input
          className="border border-zinc-300 px-3 py-2"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          required
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        PIN cuisine
        <input
          className="border border-zinc-300 px-3 py-2"
          type="password"
          value={pin}
          onChange={(e) => setPin(e.target.value)}
          required
        />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" className="bg-zinc-900 px-4 py-2 text-white">
        Ouvrir la cuisine
      </button>
    </form>
  );
}
