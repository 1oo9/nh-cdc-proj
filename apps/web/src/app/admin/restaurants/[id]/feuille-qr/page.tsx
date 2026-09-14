import { QrSheetView } from "@/components/QrSheetView";

type Props = { params: Promise<{ id: string }> };

export default async function QrSheetPage({ params }: Props) {
  const { id } = await params;
  return (
    <main className="min-h-screen bg-zinc-50 print:bg-white">
      <QrSheetView restaurantId={id} />
    </main>
  );
}
