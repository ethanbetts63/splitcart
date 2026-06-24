"use client";

import { MapPin } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { useStoreList } from "@/context/StoreListContext";
import { useDialog } from "@/context/DialogContext";

export function NavLocationButton() {
  const { selectedStoreIds, isUserDefinedList } = useStoreList();
  const { openDialog } = useDialog();

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        className="h-10 w-10 sm:h-12 sm:w-12"
        onClick={() => openDialog("Edit Location")}
      >
        <MapPin className="size-6 sm:size-7" />
        <span className="sr-only">Edit Location</span>
      </Button>
      {isUserDefinedList && selectedStoreIds.size > 0 && (
        <Badge className="absolute -right-1 -top-1 h-5 min-w-5 justify-center rounded-full bg-blue-500 px-1 font-mono tabular-nums text-white">
          {selectedStoreIds.size}
        </Badge>
      )}
    </div>
  );
}
