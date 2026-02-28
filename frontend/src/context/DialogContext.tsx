import { createContext, useContext, useState, type ReactNode } from 'react';
import type { DialogContextType } from '../types/DialogContextType';

const DialogContext = createContext<DialogContextType | undefined>(undefined);

export const DialogProvider = ({ children }: { children: ReactNode }) => {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogPage, setDialogPage] = useState('cart');

  const openDialog = (page: string) => {
    setDialogPage(page);
    setIsDialogOpen(true);
  };

  const closeDialog = () => {
    setIsDialogOpen(false);
  };

  const contextValue = {
    isDialogOpen,
    dialogPage,
    openDialog,
    closeDialog,
  };

  return (
    <DialogContext.Provider value={contextValue}>
      {children}
    </DialogContext.Provider>
  );
};

export const useDialog = () => {
  const context = useContext(DialogContext);
  if (context === undefined) {
    throw new Error('useDialog must be used within a DialogProvider');
  }
  return context;
};
