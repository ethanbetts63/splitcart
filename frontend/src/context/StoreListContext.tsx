import React, { createContext, useContext, useState, type ReactNode, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import {
  fetchActiveStoreListAPI,
  loadStoreListAPI,
  saveStoreListAPI,
  createNewStoreListAPI,
  deleteStoreListAPI,
} from '@/services/storeListApi';

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
  const { token, anonymousId } = useAuth();

  // --- State Definitions ---
  const [selectedStoreIds, setSelectedStoreIds] = useState<Set<number>>(() => {
    const saved = sessionStorage.getItem('selectedStoreIds');
    try {
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          return new Set(parsed.filter(item => typeof item === 'number'));
        }
      }
    } catch (e) {
      console.error("Failed to parse selectedStoreIds from sessionStorage", e);
    }
    return new Set<number>();
  });

  const [currentStoreListId, setCurrentStoreListId] = useState<string | null>(null);
  const [currentStoreListName, setCurrentStoreListName] = useState<string>("");
  const [userStoreLists, setUserStoreLists] = useState<SelectedStoreListType[]>([]);
  const [storeListLoading, setStoreListLoading] = useState<boolean>(true);
  const [storeListError, setStoreListError] = useState<string | null>(null);

  // --- Side Effects ---

  // Persist selected stores to sessionStorage
  useEffect(() => {
    sessionStorage.setItem('selectedStoreIds', JSON.stringify(Array.from(selectedStoreIds)));
  }, [selectedStoreIds]);

  // Self-contained initialization logic
  useEffect(() => {
    const initialize = async () => {
      if (!token && !anonymousId) {
        return; // Wait for an identity
      }
      setStoreListLoading(true);
      setStoreListError(null);
      try {
        let lists = await fetchActiveStoreListAPI(token, anonymousId);
        let activeList: SelectedStoreListType | null = null;

        if (lists.length === 0) {
          // No lists exist, so create a default one.
          const newList = await createNewStoreListAPI([], token, anonymousId);
          lists = [newList];
          activeList = newList;
        } else {
          // Lists exist, find the most recent one.
          activeList = lists.sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime())[0];
        }

        if (activeList) {
          setUserStoreLists(lists);
          setCurrentStoreListId(activeList.id);
          setCurrentStoreListName(activeList.name);

          // Only auto-load the stores from the active list if the session is empty.
          const savedSelection = sessionStorage.getItem('selectedStoreIds');
          const savedSelectionIsEmpty = !savedSelection || JSON.parse(savedSelection).length === 0;
          if (savedSelectionIsEmpty) {
            setSelectedStoreIds(new Set(activeList.stores));
          }
        }
      } catch (err: any) {
        setStoreListError(err.message);
      } finally {
        setStoreListLoading(false);
      }
    };

    initialize();
  }, [token, anonymousId]);

  // --- Context Functions ---

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

  const loadStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await loadStoreListAPI(storeListId, token, anonymousId);
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [token, anonymousId]);

  const saveStoreList = useCallback(async (name: string, storeIds: number[]) => {
    if (!currentStoreListId) return;
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await saveStoreListAPI(currentStoreListId, name, storeIds, token, anonymousId);
      setCurrentStoreListName(data.name);
      // Update the specific list in the userStoreLists array
      setUserStoreLists(prev => prev.map(list => list.id === data.id ? data : list));
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, token, anonymousId]);

  const createNewStoreList = useCallback(async (storeIds: number[]) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await createNewStoreListAPI(storeIds, token, anonymousId);
      // Set the new list as active and add it to the list array
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      setUserStoreLists(prevLists => [...prevLists, data]);
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [token, anonymousId]);

  const deleteStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      await deleteStoreListAPI(storeListId, token, anonymousId);
      const remainingLists = userStoreLists.filter(list => list.id !== storeListId);
      setUserStoreLists(remainingLists);

      // If the deleted list was the active one, load the most recent of the remaining lists
      if (currentStoreListId === storeListId) {
        if (remainingLists.length > 0) {
          const nextActiveList = remainingLists.sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime())[0];
          await loadStoreList(nextActiveList.id);
        } else {
          // If no lists remain, create a new default one
          await createNewStoreList([]);
        }
      }
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [currentStoreListId, token, anonymousId, userStoreLists, loadStoreList, createNewStoreList]);

  // The fetchActiveStoreList function is no longer needed in the public context
  const contextValue = {
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
    fetchActiveStoreList: async () => { console.warn("fetchActiveStoreList is deprecated"); },
  };

  return (
    <StoreListContext.Provider value={contextValue}>
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