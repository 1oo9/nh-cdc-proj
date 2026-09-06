import { PublicMenuView } from "@/components/PublicMenuView";

type Props = { params: Promise<{ token: string }> };

export default async function TableMenuPage({ params }: Props) {
  const { token } = await params;
  return (
    <main className="min-h-screen bg-zinc-50">
      <PublicMenuView token={token} />
    </main>
  );
}
