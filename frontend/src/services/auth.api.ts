import { type SelectedStoreListType } from '@/context/StoreListContext';
import { type Cart } from '@/types';
import { getAuthHeaders } from '@/lib/utils';

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