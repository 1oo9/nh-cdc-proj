import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { QrSheetView } from "./QrSheetView";

const router = { push: vi.fn(), replace: vi.fn() };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
  useParams: () => ({ id: "resto-1" }),
}));

describe("QrSheetView", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem("nh_admin_token", "admin-token");
    router.replace.mockReset();
  });

  it("shows printable QR cards for demo tables", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          restaurant_name: "Chicken Street Paris",
          tables: [
            {
              id: "t12",
              label: "12",
              public_token: "tok12",
              menu_url: "http://localhost:3000/t/tok12",
              qr_png_base64: "aaa",
            },
            {
              id: "t14",
              label: "14",
              public_token: "tok14",
              menu_url: "http://localhost:3000/t/tok14",
              qr_png_base64: "bbb",
            },
          ],
        }),
      }),
    );

    render(<QrSheetView restaurantId="resto-1" />);

    expect(await screen.findByText("Chicken Street Paris")).toBeInTheDocument();
    expect(screen.getByText(/Table 12/)).toBeInTheDocument();
    expect(screen.getByText(/Table 14/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Imprimer/i })).toBeInTheDocument();
    const images = screen.getAllByRole("img");
    expect(images).toHaveLength(2);
    expect(images[0]).toHaveAttribute("src", "data:image/png;base64,aaa");
  });
});
