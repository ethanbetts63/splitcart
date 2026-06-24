"use client";

import { usePathname } from "next/navigation";
import { useCart } from "@/context/CartContext";
import { useDialog } from "@/context/DialogContext";
import NextButton from "@/components/NextButton";

const SHOW_NEXT_PATHS = new Set(["/", "/search", "/bargains"]);

export function FloatingNextButton() {
  const pathname = usePathname() ?? "";
  const { currentCart } = useCart();
  const { isDialogOpen } = useDialog();

  const cartTotal = currentCart?.items.length ?? 0;

  const shouldShow =
    (SHOW_NEXT_PATHS.has(pathname) ||
      pathname.startsWith("/categories/") ||
      pathname.startsWith("/product/")) &&
    cartTotal > 0 &&
    !isDialogOpen;

  if (!shouldShow) return null;

  return (
    <NextButton className="fixed bottom-8 right-8 z-50 h-16 w-16 rounded-full shadow-lg" />
  );
}
