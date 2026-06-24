"use client";

import { useDialog } from "@/context/DialogContext";
import { SettingsDialog } from "@/components/settings-dialog";

export function SettingsDialogWrapper() {
  const { isDialogOpen, dialogPage, closeDialog } = useDialog();

  return (
    <SettingsDialog
      open={isDialogOpen}
      onOpenChange={(isOpen) => { if (!isOpen) closeDialog(); }}
      defaultPage={dialogPage}
    />
  );
}
