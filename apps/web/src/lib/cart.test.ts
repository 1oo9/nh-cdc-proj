import { describe, expect, it } from "vitest";

import { cartTotalCents, type CartItem } from "./cart";

describe("cartTotalCents", () => {
  it("sums unit prices times quantities", () => {
    const items: CartItem[] = [
      {
        productId: "1",
        name: "Chicken Burger",
        quantity: 2,
        optionIds: [],
        optionNames: ["fromage"],
        unitPriceCents: 1350,
      },
      {
        productId: "2",
        name: "Frites",
        quantity: 1,
        optionIds: [],
        optionNames: [],
        unitPriceCents: 350,
      },
    ];
    expect(cartTotalCents(items)).toBe(3050);
  });
});
