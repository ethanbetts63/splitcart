import React, { createContext, useContext, useState, ReactNode, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

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

// New type for SelectedStoreList
export type SelectedStoreListType = {
  id: string; // UUID
  name: string;
  stores: number[]; // Array of store IDs
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

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

  // New state for SelectedStoreList management
  currentStoreListId: string | null;
  setCurrentStoreListId: React.Dispatch<React.SetStateAction<string | null>>;
  currentStoreListName: string;
  setCurrentStoreListName: React.Dispatch<React.SetStateAction<string>>;
  userStoreLists: SelectedStoreListType[];
  setUserStoreLists: React.Dispatch<React.SetStateAction<SelectedStoreListType[]>>;
  storeListLoading: boolean;
  setStoreListLoading: React.Dispatch<React.SetStateAction<boolean>>;
  storeListError: string | null;
  setStoreListError: React.Dispatch<React.SetStateAction<string | null>>;

  // New functions for SelectedStoreList operations
  loadStoreList: (storeListId: string) => Promise<void>;
  saveStoreList: (name: string, storeIds: number[]) => Promise<void>;
  createNewStoreList: (storeIds: number[]) => Promise<void>;
  deleteStoreList: (storeListId: string) => Promise<void>;
  fetchUserStoreLists: () => Promise<void>;
}

// --- Context Creation ---
const StoreContext = createContext<StoreContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreProvider = ({ children }: { children: ReactNode }) => {
  const { token, isAuthenticated, anonymousId } = useAuth();

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

  // New state for SelectedStoreList management
  const [currentStoreListId, setCurrentStoreListId] = useState<string | null>(null);
  const [currentStoreListName, setCurrentStoreListName] = useState<string>('Current Selection');
  const [userStoreLists, setUserStoreLists] = useState<SelectedStoreListType[]>([]);
  const [storeListLoading, setStoreListLoading] = useState<boolean>(false);
  const [storeListError, setStoreListError] = useState<string | null>(null);

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

  const getAuthHeaders = useCallback(() => {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    } else if (anonymousId) {
      headers['X-Anonymous-ID'] = anonymousId; // Assuming anonymousId is sent via a custom header
    }
    return headers;
  }, [token, anonymousId]);

  const fetchUserStoreLists = useCallback(async () => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const response = await fetch('/api/store-lists/', {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch store lists.');
      }
      const data: SelectedStoreListType[] = await response.json();
      if (Array.isArray(data)) {
        setUserStoreLists(data);
      } else {
        setUserStoreLists([]); // Set to empty array if response is not an array
      }
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [getAuthHeaders]);

  const loadStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const response = await fetch(`/api/store-lists/${storeListId}/`, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to load store list.');
      }
      const data: SelectedStoreListType = await response.json();
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores)); // Update selectedStoreIds
      // Also update postcode, radius, selectedCompanies if these are part of the store list
      // For now, assuming store list only contains store IDs
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [getAuthHeaders, setSelectedStoreIds]);

  const saveStoreList = useCallback(async (name: string, storeIds: number[]) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const method = currentStoreListId ? 'PUT' : 'POST';
      const url = currentStoreListId ? `/api/store-lists/${currentStoreListId}/` : '/api/store-lists/';
      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify({ name, stores: storeIds }),
      });
      if (!response.ok) {
        throw new Error('Failed to save store list.');
      }
      const data: SelectedStoreListType = await response.json();
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      fetchUserStoreLists(); // Refresh the list of user's store lists
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, getAuthHeaders, fetchUserStoreLists]);

  const createNewStoreList = useCallback(async (storeIds: number[]) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const response = await fetch('/api/store-lists/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ stores: storeIds }),
      });
      if (!response.ok) {
        throw new Error('Failed to create new store list.');
      }
      const data: SelectedStoreListType = await response.json();
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      fetchUserStoreLists(); // Refresh the list of user's store lists
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [getAuthHeaders, setSelectedStoreIds, fetchUserStoreLists]);

  const deleteStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const response = await fetch(`/api/store-lists/${storeListId}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to delete store list.');
      }
      // If the deleted list was the current one, clear current selection
      if (currentStoreListId === storeListId) {
        setCurrentStoreListId(null);
        setCurrentStoreListName('Current Selection');
        setSelectedStoreIds(new Set()); // Clear selected stores
      }
      fetchUserStoreLists(); // Refresh the list of user's store lists
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, getAuthHeaders, setSelectedStoreIds, fetchUserStoreLists]);

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
      setMapCenter,
      currentStoreListId,
      setCurrentStoreListId,
      currentStoreListName,
      setCurrentStoreListName,
      userStoreLists,
      setUserStoreLists,
      storeListLoading,
      setStoreListLoading,
      storeListError,
      setStoreListError,
      loadStoreList,
      saveStoreList,
      createNewStoreList,
      deleteStoreList,
      fetchUserStoreLists
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