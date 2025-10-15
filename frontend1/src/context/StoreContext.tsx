import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

// --- Type Definitions ---
// These types are now managed globally by this context
type Store = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

type MapCenter = {
  latitude: number;
  longitude: number;
  radius: number;
} | null;

interface StoreContextType {
  // Original selection state
  selectedStoreIds: Set<number>;
  setSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  handleStoreSelect: (storeId: number) => void;

  // New state for persisting search session
  stores: Store[] | null;
  setStores: React.Dispatch<React.SetStateAction<Store[] | null>>;
  postcode: string;
  setPostcode: React.Dispatch<React.SetStateAction<string>>;
  radius: number;
  setRadius: React.Dispatch<React.SetStateAction<number>>;
  selectedCompanies: string[];
  setSelectedCompanies: React.Dispatch<React.SetStateAction<string[]>>;
  mapCenter: MapCenter;
  setMapCenter: React.Dispatch<React.SetStateAction<MapCenter>>;
}

// --- Context Creation ---
const StoreContext = createContext<StoreContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreProvider = ({ children }: { children: ReactNode }) => {
  // Original selection state
  const [selectedStoreIds, setSelectedStoreIds] = useState(() => {
    const saved = sessionStorage.getItem('selectedStoreIds');
    if (saved) {
      return new Set(JSON.parse(saved));
    }
    return new Set<number>();
  });

  useEffect(() => {
    sessionStorage.setItem('selectedStoreIds', JSON.stringify(Array.from(selectedStoreIds)));
  }, [selectedStoreIds]);

  // New state for persisting search session
  const [stores, setStores] = useState<Store[] | null>(() => {
    const saved = sessionStorage.getItem('stores');
    return saved ? JSON.parse(saved) : null;
  });

  useEffect(() => {
    if (stores) {
      sessionStorage.setItem('stores', JSON.stringify(stores));
    }
  }, [stores]);
  const [postcode, setPostcode] = useState(() => {
    return sessionStorage.getItem('postcode') || '5000';
  });

  useEffect(() => {
    sessionStorage.setItem('postcode', postcode);
  }, [postcode]);
  const [radius, setRadius] = useState(() => {
    const saved = sessionStorage.getItem('radius');
    return saved ? JSON.parse(saved) : 5;
  });

  useEffect(() => {
    sessionStorage.setItem('radius', JSON.stringify(radius));
  }, [radius]);
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>(() => {
    const saved = sessionStorage.getItem('selectedCompanies');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    sessionStorage.setItem('selectedCompanies', JSON.stringify(selectedCompanies));
  }, [selectedCompanies]);
  const [mapCenter, setMapCenter] = useState<MapCenter>(() => {
    const saved = sessionStorage.getItem('mapCenter');
    if (saved) {
      return JSON.parse(saved);
    }
    return { latitude: -34.9285, longitude: 138.6007, radius: 5 };
  });

  useEffect(() => {
    if (mapCenter) {
      sessionStorage.setItem('mapCenter', JSON.stringify(mapCenter));
    }
  }, [mapCenter]);

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
    <StoreContext.Provider value={{
      selectedStoreIds, 
      setSelectedStoreIds, 
      handleStoreSelect,
      stores,
      setStores,
      postcode,
      setPostcode,
      radius,
      setRadius,
      selectedCompanies,
      setSelectedCompanies,
      mapCenter,
      setMapCenter
    }}>
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