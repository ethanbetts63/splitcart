
import { type SelectedStoreListType } from '@/context/StoreListContext';

const getAuthHeaders = (token: string | null, anonymousId: string | null): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Token ${token}`;
  } else if (anonymousId) {
    headers['X-Anonymous-ID'] = anonymousId;
  }
  return headers;
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

  const response = await fetch(url, {
    headers: getAuthHeaders(token, anonymousId),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch store lists.');
  }
  return response.json();
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
    const response = await fetch(url, {
        method,
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify({ name, stores: storeIds }),
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
