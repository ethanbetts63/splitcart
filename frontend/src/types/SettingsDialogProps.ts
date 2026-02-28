export interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultPage?: string;
}
