import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';
import type { Product } from '@/types/Product';

interface SubstitutionContextType {
  itemsToReview: Product[];
  setItemsToReview: (items: Product[]) => void;
  substitutes: Record<number, Product[]>;
  selections: Record<number, Product[]>;
  fetchSubstitutes: (product: Product, storeIds: number[]) => void;
  updateSelections: (originalProductId: number, selectedProducts: Product[]) => void;
  currentItemIndex: number;
  setCurrentItemIndex: (index: number) => void;
}

const SubstitutionContext = createContext<SubstitutionContextType | undefined>(undefined);

export const SubstitutionProvider = ({ children }: { children: ReactNode }) => {
  const [itemsToReview, setItemsToReview] = useState<Product[]>([]);
  const [substitutes, setSubstitutes] = useState<Record<number, Product[]>>({});
  const [selections, setSelections] = useState<Record<number, Product[]>>({});
  const [currentItemIndex, setCurrentItemIndex] = useState(0);

  const fetchSubstitutes = useCallback(async (product: Product, storeIds: number[]) => {
    if (!product || !storeIds || storeIds.length === 0) return;
    try {
      const ids = storeIds.join(',');
      const url = `/api/products/${product.id}/substitutes/?store_ids=${ids}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const subs = await response.json();
      setSubstitutes(prev => ({ ...prev, [product.id]: subs }));
    } catch (error) {
      console.error(`Error fetching substitutes for product ${product.id}:`, error);
      setSubstitutes(prev => ({ ...prev, [product.id]: [] }));
    }
  }, []);

  const updateSelections = (originalProductId: number, selectedProducts: Product[]) => {
    setSelections(prev => ({ ...prev, [originalProductId]: selectedProducts }));
  };

  const value = {
    itemsToReview,
    setItemsToReview,
    substitutes,
    selections,
    fetchSubstitutes,
    updateSelections,
    currentItemIndex,
    setCurrentItemIndex,
  };

  return (
    <SubstitutionContext.Provider value={value}>
      {children}
    </SubstitutionContext.Provider>
  );
};

export const useSubstitutions = () => {
  const context = useContext(SubstitutionContext);
  if (context === undefined) {
    throw new Error('useSubstitutions must be used within a SubstitutionProvider');
  }
  return context;
};
