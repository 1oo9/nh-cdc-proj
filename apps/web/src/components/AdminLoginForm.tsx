"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function AdminLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@nh.example");
  const [password, setPassword] = useState("nh-admin");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const response = await fetch(`${API_URL}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      setError("Identifiants invalides");
      return;
    }
    const body = (await response.json()) as { access_token: string };
    window.localStorage.setItem("nh_admin_token", body.access_token);
    router.push("/admin");
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto flex w-full max-w-sm flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm">
        Email
        <input
          className="border border-zinc-300 px-3 py-2"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Mot de passe
        <input
          className="border border-zinc-300 px-3 py-2"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" className="bg-zinc-900 px-4 py-2 text-white">
        Connexion
      </button>
    </form>
  );
}
