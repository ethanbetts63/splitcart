export interface DialogContextType {
  isDialogOpen: boolean;
  dialogPage: string;
  openDialog: (page: string) => void;
  closeDialog: () => void;
}
