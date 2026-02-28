import { type ApiClient } from './apiClient';
import type { PaginatedProductResponse } from '../types/PaginatedProductResponse';

/**
 * Fetches products from a given URL (which includes search/filter query params).
 * The URL should be a relative API path, e.g., /api/products/?search=...
 */
export const fetchProductsAPI = (apiClient: ApiClient, url: string): Promise<PaginatedProductResponse> => {
  return apiClient.get<PaginatedProductResponse>(url);
};
