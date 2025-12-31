import React, { createContext, useContext, useState, type ReactNode, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { type SelectedStoreListType } from '../types';
import * as storeListApi from '../services/storeList.api';
import { createApiClient, ApiError } from '../services/apiClient';
import { useCart } from './CartContext';

// Type for the anchor map
export type AnchorMap = { [storeId: number]: number };

interface StoreListContextType {
  selectedStoreIds: Set<number>;
  setSelectedStoreIds: React.Dispatch<React.SetStateAction<Set<number>>>;
  handleStoreSelect: (storeId: number) => void;
  currentStoreListId: string | null;
  setCurrentStoreListId: React.Dispatch<React.SetStateAction<string | null>>;
  currentStoreListName: string;
  setCurrentStoreListName: React.Dispatch<React.SetStateAction<string>>;
  isUserDefinedList: boolean;
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
  anchorStoreMap: AnchorMap | null;
  setAnchorStoreMap: React.Dispatch<React.SetStateAction<AnchorMap | null>>;
}

// --- Context Creation ---
const StoreListContext = createContext<StoreListContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreListProvider = ({ children }: { children: ReactNode }) => {
  const { token, anonymousId, isLoading: isAuthLoading } = useAuth();
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);
  const { updateCartStoreList } = useCart();

  // --- State Definitions ---
  const [selectedStoreIds, setSelectedStoreIds] = useState<Set<number>>(() => new Set<number>());
  const [anchorStoreMap, setAnchorStoreMap] = useState<AnchorMap | null>(null);
  const [currentStoreListId, setCurrentStoreListId] = useState<string | null>(null);
  const [currentStoreListName, setCurrentStoreListName] = useState<string>("");
  const [isUserDefinedList, setIsUserDefinedList] = useState<boolean>(false);
  const [userStoreLists, setUserStoreLists] = useState<SelectedStoreListType[]>([]);
  const [storeListLoading, setStoreListLoading] = useState<boolean>(true);
  const [storeListError, setStoreListError] = useState<string | null>(null);

  // --- Side Effects ---

  // Fetch initial data on mount
  useEffect(() => {
    const fetchInitialData = async () => {
      if (isAuthLoading) return;

      setStoreListLoading(true);
      try {
        const activeData = await storeListApi.fetchActiveStoreListDataAPI(apiClient);
        const storeList = activeData.store_list;
        
        if (storeList) {
            setUserStoreLists([storeList]);
            setCurrentStoreListId(storeList.id);
            setCurrentStoreListName(storeList.name);
            setIsUserDefinedList(storeList.is_user_defined);
            setSelectedStoreIds(new Set(storeList.stores));
            updateCartStoreList(storeList.id);
        }
        setAnchorStoreMap(activeData.anchor_map ?? null);

      } catch (error: any) {
        if (error instanceof ApiError && error.statusCode === 404) {
          setCurrentStoreListId(null);
          setSelectedStoreIds(new Set());
          setAnchorStoreMap(null);
        } else {
          console.error("Failed to fetch initial store list data:", error);
          setStoreListError("Could not load initial store data.");
        }
      } finally {
        setStoreListLoading(false);
      }
    };

    fetchInitialData();
  }, [apiClient, isAuthLoading]);


  // Autosave store selection
  useEffect(() => {
    // This effect should ideally be refactored to be more explicit,
    // perhaps with a "dirty" flag, but for now we keep the logic.
    // A simple guard against running on initial load or when no list is active.
    if (storeListLoading || !currentStoreListId) {
      return;
    }

    saveStoreList(currentStoreListName, Array.from(selectedStoreIds));
  }, [selectedStoreIds]);


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
      const data = await storeListApi.loadStoreListAPI(apiClient, storeListId);
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      setIsUserDefinedList(data.is_user_defined);
      updateCartStoreList(data.id);
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient, updateCartStoreList]);

  const createNewStoreList = useCallback(async (storeIds: number[]) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await storeListApi.createNewStoreListAPI(apiClient, storeIds);
      setCurrentStoreListId(data.id);
      setCurrentStoreListName(data.name);
      setSelectedStoreIds(new Set(data.stores));
      setIsUserDefinedList(data.is_user_defined);
      setUserStoreLists(prevLists => [...prevLists, data]);
      updateCartStoreList(data.id);
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient, updateCartStoreList]);

  const saveStoreList = useCallback(async (name: string, storeIds: number[]) => {
    if (!currentStoreListId) {
        if (storeIds.length > 0) {
            await createNewStoreList(storeIds);
        }
        return;
    }

    setStoreListLoading(true);
    setStoreListError(null);
    try {
      const data = await storeListApi.saveStoreListAPI(apiClient, currentStoreListId, name, storeIds);
      setCurrentStoreListName(data.name);
      setIsUserDefinedList(data.is_user_defined);
      setUserStoreLists(prev => prev.map(list => list.id === data.id ? data : list));
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient, currentStoreListId, createNewStoreList]);

  const deleteStoreList = useCallback(async (storeListId: string) => {
    setStoreListLoading(true);
    setStoreListError(null);
    try {
      await storeListApi.deleteStoreListAPI(apiClient, storeListId);
      const remainingLists = userStoreLists.filter(list => list.id !== storeListId);
      setUserStoreLists(remainingLists);

      if (currentStoreListId === storeListId) {
        if (remainingLists.length > 0) {
          const nextActiveList = remainingLists.sort((a, b) => new Date(b.last_used_at).getTime() - new Date(a.last_used_at).getTime())[0];
          await loadStoreList(nextActiveList.id);
        } else {
          await createNewStoreList([]);
        }
      }
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient, currentStoreListId, userStoreLists, loadStoreList, createNewStoreList]);

  // The fetchActiveStoreList function is no longer needed in the public context
  const contextValue = {
    selectedStoreIds,
    setSelectedStoreIds,
    handleStoreSelect,
    currentStoreListId,
    setCurrentStoreListId,
    currentStoreListName,
    setCurrentStoreListName,
    isUserDefinedList,
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
    anchorStoreMap,
    setAnchorStoreMap,
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