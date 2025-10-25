import { type SelectedStoreListType } from '@/context/StoreListContext';
import { type Cart } from '@/types';

const getAuthHeaders = (token: string | null, anonymousId: string | null): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Token ${token}`;
  } else if (anonymousId !== null) {
    headers['X-Anonymous-ID'] = anonymousId;
  }
  return headers;
};

export interface InitialSetupData {
  cart: Cart;
  store_list: SelectedStoreListType;
  anonymous_id?: string; // Add anonymous_id as an optional field
}

export const performInitialSetupAPI = async (token: string | null, anonymousId: string | null): Promise<InitialSetupData> => {
  const response = await fetch('/api/initial-setup/', {
    method: 'POST',
    headers: getAuthHeaders(token, anonymousId),
  });
  if (!response.ok) {
    throw new Error('Failed to perform initial setup.');
  }
  return response.json();
};
