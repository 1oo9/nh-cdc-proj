"use client";

export type CartItem = {
  productId: string;
  name: string;
  quantity: number;
  optionIds: string[];
  optionNames: string[];
  unitPriceCents: number;
};

function cartKey(token: string) {
  return `nh_cart_${token}`;
}

export function readCart(token: string): CartItem[] {
  if (typeof window === "undefined") return [];
  const raw = window.sessionStorage.getItem(cartKey(token));
  if (!raw) return [];
  try {
    return JSON.parse(raw) as CartItem[];
  } catch {
    return [];
  }
}

export function writeCart(token: string, items: CartItem[]) {
  window.sessionStorage.setItem(cartKey(token), JSON.stringify(items));
}

export function clearCart(token: string) {
  window.sessionStorage.removeItem(cartKey(token));
}

export function cartTotalCents(items: CartItem[]) {
  return items.reduce((sum, item) => sum + item.unitPriceCents * item.quantity, 0);
}
