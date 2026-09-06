import { ConfirmationView } from "@/components/ConfirmationView";

type Props = { params: Promise<{ token: string; orderId: string }> };

export default async function ConfirmationPage({ params }: Props) {
  const { token, orderId } = await params;
  return (
    <main className="min-h-screen bg-zinc-50">
      <ConfirmationView token={token} orderId={orderId} />
    </main>
  );
}
