
import { type SelectedStoreListType } from '@/types';
import { getAuthHeaders } from '@/lib/utils';

export const fetchActiveStoreListAPI = async (token: string | null, anonymousId: string | null): Promise<SelectedStoreListType[]> => {
  let url = '';
  if (token) {
    url = '/api/store-lists/';
  } else if (anonymousId) {
    url = `/api/store-lists/?anonymous_id=${anonymousId}`;
  } else {
    return Promise.resolve([]);
  }

  const response = await fetch(url, {
    headers: getAuthHeaders(token, anonymousId),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch store lists.');
  }

  const data = await response.json();

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
    const response = await fetch(`/api/store-lists/${storeListId}/`, {
        headers: getAuthHeaders(token, anonymousId),
    });
    if (!response.ok) {
        throw new Error('Failed to load store list.');
    }
    return response.json();
};

export const saveStoreListAPI = async (
    listId: string | null,
    name: string,
    storeIds: number[],
    token: string | null,
    anonymousId: string | null
): Promise<SelectedStoreListType> => {
    const method = listId ? 'PUT' : 'POST';
    const url = listId ? `/api/store-lists/${listId}/` : '/api/store-lists/';
    const requestBody: { name?: string; stores: number[] } = { stores: storeIds };

    // Only include name if the user is authenticated (has a token)
    if (token) {
        requestBody.name = name;
    }

    const response = await fetch(url, {
        method,
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify(requestBody),
    });
    if (!response.ok) {
        throw new Error('Failed to save store list.');
    }
    return response.json();
};

export const createNewStoreListAPI = async (
    storeIds: number[],
    token: string | null,
    anonymousId: string | null
): Promise<SelectedStoreListType> => {
    const response = await fetch('/api/store-lists/', {
        method: 'POST',
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify({ stores: storeIds }),
    });
    if (!response.ok) {
        throw new Error('Failed to create new store list.');
    }
    return response.json();
};

export const deleteStoreListAPI = async (
    storeListId: string,
    token: string | null,
    anonymousId: string | null
): Promise<void> => {
    const response = await fetch(`/api/store-lists/${storeListId}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(token, anonymousId),
    });
    if (!response.ok) {
        throw new Error('Failed to delete store list.');
    }
};