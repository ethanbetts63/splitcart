import React, { createContext, useContext, useState, type ReactNode, useEffect } from 'react';

// --- Type Definitions ---
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

interface StoreSearchContextType {
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
const StoreSearchContext = createContext<StoreSearchContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreSearchProvider = ({ children }: { children: ReactNode }) => {
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

  return (
    <StoreSearchContext.Provider value={{
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
    </StoreSearchContext.Provider>
  );
};

// --- Custom Hook ---
export const useStoreSearch = () => {
  const context = useContext(StoreSearchContext);
  if (context === undefined) {
    throw new Error('useStoreSearch must be used within a StoreSearchProvider');
  }
  return context;
};