"use client";

import { ShoppingCart } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { useCart } from "@/context/CartContext";
import { useDialog } from "@/context/DialogContext";
import { useStoreList } from "@/context/StoreListContext";

export function NavCartButton() {
  const { currentCart } = useCart();
  const { openDialog } = useDialog();
  const { selectedStoreIds } = useStoreList();

  const cartTotal = currentCart?.items.length ?? 0;

  const handleClick = () => {
    if (selectedStoreIds.size === 0) {
      openDialog("Edit Location");
    } else {
      openDialog("cart");
    }
  };

  return (
    <div className="relative">
      <Button variant="ghost" size="icon" className="h-10 w-10 sm:h-12 sm:w-12" onClick={handleClick}>
        <ShoppingCart className="size-6 sm:size-7" />
        <span className="sr-only">Open cart</span>
      </Button>
      {cartTotal > 0 && (
        <Badge
          variant="destructive"
          className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full px-1 font-mono tabular-nums"
        >
          {cartTotal}
        </Badge>
      )}
    </div>
  );
}
