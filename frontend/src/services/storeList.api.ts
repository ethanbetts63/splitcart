import { type SelectedStoreListType } from '../types';
import { type AnchorMap } from '../context/StoreListContext';
import { createApiClient } from './apiClient'; // Import ApiClient

// The expected data shape from the new /api/store-lists/active/ endpoint
export interface ActiveStoreListData {
  store_list: SelectedStoreListType;
  anchor_map: AnchorMap;
}

export const fetchActiveStoreListDataAPI = async (token: string | null, anonymousId: string | null): Promise<ActiveStoreListData> => {
  const apiClient = createApiClient(token, anonymousId);
  return apiClient.get<ActiveStoreListData>('/api/store-lists/active/');
};

export const fetchActiveStoreListAPI = async (token: string | null, anonymousId: string | null): Promise<SelectedStoreListType[]> => {
  let url = '';
  if (token) {
    url = '/api/store-lists/';
  } else if (anonymousId) {
    url = `/api/store-lists/?anonymous_id=${anonymousId}`;
  } else {
    return Promise.resolve([]);
  }

  const apiClient = createApiClient(token, anonymousId);
  const data = await apiClient.get<SelectedStoreListType[] | { results: SelectedStoreListType[] }>(url);

  // Handle Django Rest Framework's paginated response
  if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
    return data.results;
  }

  // Handle the case where the API returns a direct array (e.g., for anonymous users)
  if (Array.isArray(data)) {
    return data;
  }

  // If the response is neither, log an error and return an empty array to prevent crashes
  console.error("API response for store lists was not in the expected format (paginated object or direct array):", data);
  return [];
};

export const loadStoreListAPI = async (storeListId: string, token: string | null, anonymousId: string | null): Promise<SelectedStoreListType> => {
    const apiClient = createApiClient(token, anonymousId);
    return apiClient.get<SelectedStoreListType>(`/api/store-lists/${storeListId}/`);
};

export const saveStoreListAPI = async (
    listId: string | null,
    name: string,
    storeIds: number[],
    token: string | null,
    anonymousId: string | null
): Promise<SelectedStoreListType> => {
    const apiClient = createApiClient(token, anonymousId);
    const method = listId ? 'PUT' : 'POST';
    const url = listId ? `/api/store-lists/${listId}/` : '/api/store-lists/';
    const requestBody: { name?: string; stores: number[] } = { stores: storeIds };

    // Only include name if the user is authenticated (has a token)
    if (token) {
        requestBody.name = name;
    }

    if (method === 'PUT') {
        return apiClient.put<SelectedStoreListType>(url, requestBody);
    } else {
        return apiClient.post<SelectedStoreListType>(url, requestBody);
    }
};

export const createNewStoreListAPI = async (
    storeIds: number[],
    token: string | null,
    anonymousId: string | null
): Promise<SelectedStoreListType> => {
    const apiClient = createApiClient(token, anonymousId);
    return apiClient.post<SelectedStoreListType>('/api/store-lists/', { stores: storeIds });
};
export const deleteStoreListAPI = async (
    storeListId: string,
    token: string | null,
    anonymousId: string | null
): Promise<void> => {
    const apiClient = createApiClient(token, anonymousId);
    await apiClient.delete(`/api/store-lists/${storeListId}/`);
};