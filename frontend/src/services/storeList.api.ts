import { type SelectedStoreListType } from '../types';
import type { ActiveStoreListData } from '../types/ActiveStoreListData';
import { type ApiClient } from './apiClient';

export const fetchActiveStoreListDataAPI = (apiClient: ApiClient): Promise<ActiveStoreListData> => {
  return apiClient.get<ActiveStoreListData>('/api/store-lists/active/');
};

export const fetchUserStoreListsAPI = async (apiClient: ApiClient): Promise<SelectedStoreListType[]> => {
  const url = '/api/store-lists/';
  const data = await apiClient.get<SelectedStoreListType[] | { results: SelectedStoreListType[] }>(url);

  if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
    return data.results;
  }
  if (Array.isArray(data)) {
    return data;
  }

  console.error("API response for store lists was not in the expected format:", data);
  return [];
};

export const loadStoreListAPI = (apiClient: ApiClient, storeListId: string): Promise<SelectedStoreListType> => {
    return apiClient.get<SelectedStoreListType>(`/api/store-lists/${storeListId}/`);
};

export const saveStoreListAPI = (
    apiClient: ApiClient,
    listId: string | null,
    name: string,
    storeIds: number[]
): Promise<SelectedStoreListType> => {
    const method = listId ? 'PUT' : 'POST';
    const url = listId ? `/api/store-lists/${listId}/` : '/api/store-lists/';
    const requestBody: { name?: string; stores: number[] } = { stores: storeIds };

    // Name is only included for authenticated users, which is determined by the ApiClient instance
    if (apiClient.isAuthenticated()) { // Assuming ApiClient has such a method
        requestBody.name = name;
    }

    if (method === 'PUT') {
        return apiClient.put<SelectedStoreListType>(url, requestBody);
    } else {
        return apiClient.post<SelectedStoreListType>(url, requestBody);
    }
};

export const createNewStoreListAPI = (
    apiClient: ApiClient,
    storeIds: number[]
): Promise<SelectedStoreListType> => {
    return apiClient.post<SelectedStoreListType>('/api/store-lists/', { stores: storeIds });
};

export const deleteStoreListAPI = (
    apiClient: ApiClient,
    storeListId: string
): Promise<void> => {
    return apiClient.delete(`/api/store-lists/${storeListId}/`);
};