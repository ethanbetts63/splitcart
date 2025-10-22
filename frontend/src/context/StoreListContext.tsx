import React, { createContext, useContext, useState, type ReactNode, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

// --- Type Definitions ---
export type SelectedStoreListType = {
  id: string; // UUID
  name: string;
  stores: number[]; // Array of store IDs
  created_at: string;
  updated_at: string;
  last_used_at: string;
};

interface StoreListContextType {
  selectedStoreIds: Set<number>;
  setSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  handleStoreSelect: (storeId: number) => void;
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
  loadStoreList: (storeListId: string) => Promise<void>;
  saveStoreList: (name: string, storeIds: number[]) => Promise<void>;
  createNewStoreList: (storeIds: number[]) => Promise<void>;
  deleteStoreList: (storeListId: string) => Promise<void>;
  fetchActiveStoreList: () => Promise<void>;
}

// --- Context Creation ---
const StoreListContext = createContext<StoreListContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreListProvider = ({ children }: { children: ReactNode }) => {
  const { token, isAuthenticated, anonymousId } = useAuth();

  const [selectedStoreIds, setSelectedStoreIds] = useState<Set<number>>(() => {
    const saved = sessionStorage.getItem('selectedStoreIds');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed)) {
        return new Set(parsed.filter(item => typeof item === 'number'));
      }
    }
    return new Set<number>();
  });

  useEffect(() => {
    sessionStorage.setItem('selectedStoreIds', JSON.stringify(Array.from(selectedStoreIds)));
  }, [selectedStoreIds]);

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
      headers['X-Anonymous-ID'] = anonymousId;
    }
    return headers;
  }, [token, anonymousId]);

  const fetchActiveStoreList = useCallback(async () => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      let url = '';
      if (isAuthenticated) {
        url = '/api/store-lists/';
      } else if (anonymousId) {
        url = `/api/store-lists/?anonymous_id=${anonymousId}`;
      } else {
        setStoreListLoading(false);
        return;
      }

      const response = await fetch(url, {
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch store lists.');
      }
      const data: SelectedStoreListType[] = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        setUserStoreLists(data);
        const activeList = data.sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime())[0];
        setCurrentStoreListId(activeList.id);
        setCurrentStoreListName(activeList.name);
        setSelectedStoreIds(new Set(activeList.stores));
      } else {
        setUserStoreLists([]);
        setCurrentStoreListId(null);
        setCurrentStoreListName('Current Selection');
        setSelectedStoreIds(new Set());
      }
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [isAuthenticated, anonymousId, getAuthHeaders, setSelectedStoreIds, setCurrentStoreListId, setCurrentStoreListName]);

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
      setSelectedStoreIds(new Set(data.stores));
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
      fetchActiveStoreList();
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, getAuthHeaders, fetchActiveStoreList]);

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
      fetchActiveStoreList();
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [getAuthHeaders, setSelectedStoreIds, fetchActiveStoreList]);

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
      if (currentStoreListId === storeListId) {
        setCurrentStoreListId(null);
        setCurrentStoreListName('Current Selection');
        setSelectedStoreIds(new Set());
      }
      fetchActiveStoreList();
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, getAuthHeaders, setSelectedStoreIds, fetchActiveStoreList]);

  return (
    <StoreListContext.Provider value={{
      selectedStoreIds,
      setSelectedStoreIds,
      handleStoreSelect,
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
      fetchActiveStoreList
    }}>
      {children}
    </StoreListContext.Provider>
  );
};

// --- Custom Hook ---
export const useStoreList = () => {
  const context = useContext(StoreListContext);
  if (context === undefined) {
    throw new Error('useStoreList must be used within a StoreListProvider');
  }
  return context;
};