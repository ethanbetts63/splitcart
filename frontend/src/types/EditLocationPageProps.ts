import type { Dispatch, SetStateAction } from 'react';

export interface EditLocationPageProps {
  localSelectedStoreIds: Set<number>;
  setLocalSelectedStoreIds: Dispatch<SetStateAction<Set<number>>>;
  onOpenChange: (open: boolean) => void;
  setHasSearchOccurred: Dispatch<SetStateAction<boolean>>;
}
