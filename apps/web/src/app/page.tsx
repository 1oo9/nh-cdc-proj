import { HealthStatus } from "@/components/HealthStatus";

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <HealthStatus />
    </main>
  );
}
