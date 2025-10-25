import { type InitialSetupData } from '@/types';
import { getAuthHeaders } from '@/lib/utils';

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