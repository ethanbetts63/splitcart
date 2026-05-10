"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { CartProvider } from "@/context/CartContext";
import { DialogProvider } from "@/context/DialogContext";
import { StoreListProvider } from "@/context/StoreListContext";
import { StoreSearchProvider } from "@/context/StoreSearchContext";

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <DialogProvider>
          <CartProvider>
            <StoreListProvider>
              <StoreSearchProvider>{children}</StoreSearchProvider>
            </StoreListProvider>
          </CartProvider>
        </DialogProvider>
      </QueryClientProvider>
    </AuthProvider>
  );
}
