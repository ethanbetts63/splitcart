import { createContext, useContext, useState, type ReactNode, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { createApiClient } from '../services/apiClient';
import { searchNearbyStoresAPI } from '../services/store.api';
import { companyNames } from '../lib/companies';
import { useStoreList } from './StoreListContext';
import type { Store } from '../types/Store';
import type { MapBounds } from '../types/MapBounds';
import type { StoreSearchContextType } from '../types/StoreSearchContextType';

// --- Context Creation ---
const StoreSearchContext = createContext<StoreSearchContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreSearchProvider = ({ children }: { children: ReactNode }) => {
  const { token, anonymousId } = useAuth();
  const { setAnchorStoreMap } = useStoreList();
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

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
    return sessionStorage.getItem('postcode') || '';
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
    return [...companyNames]; // Always default to all companies selected
  });

  useEffect(() => {
    sessionStorage.setItem('selectedCompanies', JSON.stringify(selectedCompanies));
  }, [selectedCompanies]);

  const [mapBounds, setMapBounds] = useState<MapBounds>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async (): Promise<Store[] | null> => {
    if (!postcode || postcode.split(',').some(p => !/^\d{4}$/.test(p.trim()))) {
      setError("Please enter valid 4-digit postcodes.");
      return null;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const data = await searchNearbyStoresAPI(apiClient, { postcode, radius, companies: selectedCompanies });
      const fetchedStores = data.stores || [];
      const fetchedAnchorMap = data.anchor_map || {};

      setStores(fetchedStores);
      setAnchorStoreMap(fetchedAnchorMap);

      if (fetchedStores.length > 0) {
        const bounds = fetchedStores.reduce((acc, store) => {
          return [
            [Math.min(acc[0][0], store.latitude), Math.min(acc[0][1], store.longitude)],
            [Math.max(acc[1][0], store.latitude), Math.max(acc[1][1], store.longitude)],
          ];
        }, [[fetchedStores[0].latitude, fetchedStores[0].longitude], [fetchedStores[0].latitude, fetchedStores[0].longitude]]) as [[number, number], [number, number]];
        setMapBounds(bounds);
      } else {
        setMapBounds(null);
      }
      return fetchedStores;

    } catch (err: any) {
      setError(err.message);
      setStores([]);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, postcode, radius, selectedCompanies, setStores, setAnchorStoreMap, setMapBounds]);

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
      mapBounds,
      setMapBounds,
      isLoading,
      error,
      handleSearch
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