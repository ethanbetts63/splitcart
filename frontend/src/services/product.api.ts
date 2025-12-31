import { type ApiClient } from './apiClient';
import { type Product } from '../types';

type ApiResponse = {
    count: number;
    next: string | null;
    previous: string | null;
    results: Product[];
};

/**
 * Fetches products from a given URL (which includes search/filter query params).
 * The URL should be a relative API path, e.g., /api/products/?search=...
 */
export const fetchProductsAPI = (apiClient: ApiClient, url: string): Promise<ApiResponse> => {
  return apiClient.get<ApiResponse>(url);
};
