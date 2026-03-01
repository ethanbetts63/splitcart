import type { Dispatch, SetStateAction } from 'react';
import type { SelectedStoreListType } from './SelectedStoreListType';

export interface StoreListContextType {
  selectedStoreIds: Set<number>;
  setSelectedStoreIds: Dispatch<SetStateAction<Set<number>>>;
  handleStoreSelect: (storeId: number) => void;
  currentStoreListId: string | null;
  setCurrentStoreListId: Dispatch<SetStateAction<string | null>>;
  currentStoreListName: string;
  setCurrentStoreListName: Dispatch<SetStateAction<string>>;
  isUserDefinedList: boolean;
  userStoreLists: SelectedStoreListType[];
  setUserStoreLists: Dispatch<SetStateAction<SelectedStoreListType[]>>;
  storeListLoading: boolean;
  setStoreListLoading: Dispatch<SetStateAction<boolean>>;
  storeListError: string | null;
  setStoreListError: Dispatch<SetStateAction<string | null>>;
  loadStoreList: (storeListId: string) => Promise<void>;
  saveStoreList: (name: string, storeIds: number[]) => Promise<void>;
  createNewStoreList: (storeIds: number[]) => Promise<void>;
  deleteStoreList: (storeListId: string) => Promise<void>;
  fetchActiveStoreList: () => Promise<void>;
}
