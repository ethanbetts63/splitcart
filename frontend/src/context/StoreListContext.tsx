import { createContext, useContext, useState, type ReactNode, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { type SelectedStoreListType } from '../types';
import type { StoreListContextType } from '../types/StoreListContextType';
import * as storeListApi from '../services/storeList.api';
import { createApiClient } from '../services/apiClient';

// --- Context Creation ---
const StoreListContext = createContext<StoreListContextType | undefined>(undefined);

// --- Provider Component ---
export const StoreListProvider = ({ children }: { children: ReactNode }) => {
  const { token, anonymousId, isLoading: isAuthLoading } = useAuth();
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

  // --- State Definitions ---
  const [selectedStoreIds, setSelectedStoreIds] = useState<Set<number>>(() => new Set<number>());
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
            // Case for existing user with an active list
            setUserStoreLists([storeList]);
            setCurrentStoreListId(storeList.id);
            setCurrentStoreListName(storeList.name);
            setIsUserDefinedList(storeList.is_user_defined);
            setSelectedStoreIds(new Set(storeList.stores));
        } else {
            // Case for new user with no active list
            setCurrentStoreListId(null);
            setSelectedStoreIds(new Set());
            // userStoreLists is already an empty array, so no need to set
        }

      } catch (error: any) {
        // The 404 case is now handled above, so we only log other, unexpected errors.
        console.error("Failed to fetch initial store list data:", error);
        setStoreListError("Could not load initial store data.");
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
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient]);

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
    } catch (err: any) {
      setStoreListError(err.message);
    } finally {
      setStoreListLoading(false);
    }
  }, [apiClient]);

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