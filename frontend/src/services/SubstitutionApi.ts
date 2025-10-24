import type { ApiResponse } from '@/types';

export const optimizeCartAPI = async (cartId: string): Promise<ApiResponse> => {
  const response = await fetch('/api/cart/split/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cart_id: cartId }),
  });

  if (!response.ok) {
    // Consider more specific error handling based on response status
    throw new Error('Optimization failed');
  }

  const results: ApiResponse = await response.json();
  return results;
};
