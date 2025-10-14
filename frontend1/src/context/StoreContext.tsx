import React, { createContext, useContext, useState, ReactNode } from 'react';

// --- Type Definitions ---
interface StoreContextType {
  selectedStoreIds: Set<number>;
  setSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  handleStoreSelect: (storeId: number) => void;
}

// --- Context Creation ---
const StoreContext = createContext<StoreContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreProvider = ({ children }: { children: ReactNode }) => {
  const [selectedStoreIds, setSelectedStoreIds] = useState(new Set<number>());

  const handleStoreSelect = (storeId: number) => {
    setSelectedStoreIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(storeId)) {
        newSet.delete(storeId);
      } else {
        newSet.add(storeId);
      }
      return newSet;
    });
  };

  return (
    <StoreContext.Provider value={{ selectedStoreIds, setSelectedStoreIds, handleStoreSelect }}>
      {children}
    </StoreContext.Provider>
  );
};

// --- Custom Hook ---
export const useStoreSelection = () => {
  const context = useContext(StoreContext);
  if (context === undefined) {
    throw new Error('useStoreSelection must be used within a StoreProvider');
  }
  return context;
};
