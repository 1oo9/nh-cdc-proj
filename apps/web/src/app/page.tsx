import Link from "next/link";

import { HealthStatus } from "@/components/HealthStatus";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">NH — commande table</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Accès interne. Les convives passent par le QR de table.
        </p>
      </div>
      <nav className="flex flex-col gap-3 text-sm">
        <Link className="underline" href="/admin/login">
          Admin (menu & tables)
        </Link>
        <Link className="underline" href="/cuisine/login">
          Cuisine (tablette)
        </Link>
      </nav>
      <HealthStatus />
    </main>
  );
}
