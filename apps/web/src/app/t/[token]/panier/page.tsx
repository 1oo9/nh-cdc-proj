import { CartView } from "@/components/CartView";

type Props = { params: Promise<{ token: string }> };

export default async function CartPage({ params }: Props) {
  const { token } = await params;
  return (
    <main className="min-h-screen bg-zinc-50">
      <CartView token={token} />
    </main>
  );
}
