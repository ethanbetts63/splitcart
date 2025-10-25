import { type SelectedStoreListType, type Cart, type InitialSetupData } from '@/types';

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