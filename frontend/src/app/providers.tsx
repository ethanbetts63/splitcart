"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { CartProvider } from "@/context/CartContext";
import { DialogProvider } from "@/context/DialogContext";

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <DialogProvider>
          <CartProvider>
            {children}
          </CartProvider>
        </DialogProvider>
      </QueryClientProvider>
    </AuthProvider>
  );
}
