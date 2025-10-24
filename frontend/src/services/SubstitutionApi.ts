import type { ApiResponse } from '@/types';

interface OptimizationData {
  cart: { product_id: number; quantity: number; }[][];
  store_ids: number[];
  original_items: { product: { id: number; }; quantity: number; }[];
}

export const optimizeCartAPI = async (optimizationData: OptimizationData): Promise<ApiResponse> => {
  const response = await fetch('/api/cart/split/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(optimizationData),
  });

  if (!response.ok) {
    // Consider more specific error handling based on response status
    throw new Error('Optimization failed');
  }

  const results: ApiResponse = await response.json();
  return results;
};
