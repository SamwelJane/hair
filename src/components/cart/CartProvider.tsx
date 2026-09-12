"use client";

import { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import type { CartItem } from "@/lib/cart/types";

const STORAGE_KEY = "hiar-business-cart";

interface CartContextValue {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (productId: string, variantId?: string) => void;
  updateQuantity: (productId: string, variantId: string | undefined, quantity: number) => void;
  clear: () => void;
}

const CartContext = createContext<CartContextValue | null>(null);

function sameLine(a: CartItem, productId: string, variantId?: string) {
  return a.productId === productId && a.variantId === variantId;
}

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<CartItem[]>([]);
  const loaded = useRef(false);

  useEffect(() => {
    const loadCart = window.setTimeout(() => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) setItems(JSON.parse(raw));
      } catch {
        // storage unavailable or malformed, keep an empty cart
      } finally {
        loaded.current = true;
      }
    }, 0);
    return () => window.clearTimeout(loadCart);
  }, []);

  useEffect(() => {
    if (!loaded.current) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      // storage unavailable, ignore
    }
  }, [items, loaded]);

  const addItem = useCallback((item: CartItem) => {
    setItems((prev) => {
      const existing = prev.find((p) => sameLine(p, item.productId, item.variantId));
      if (existing) {
        return prev.map((p) =>
          sameLine(p, item.productId, item.variantId)
            ? { ...p, quantity: p.quantity + item.quantity }
            : p
        );
      }
      return [...prev, item];
    });
  }, []);

  const removeItem = useCallback((productId: string, variantId?: string) => {
    setItems((prev) => prev.filter((p) => !sameLine(p, productId, variantId)));
  }, []);

  const updateQuantity = useCallback(
    (productId: string, variantId: string | undefined, quantity: number) => {
      setItems((prev) =>
        prev.map((p) => (sameLine(p, productId, variantId) ? { ...p, quantity } : p))
      );
    },
    []
  );

  const clear = useCallback(() => setItems([]), []);

  return (
    <CartContext.Provider value={{ items, addItem, removeItem, updateQuantity, clear }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
