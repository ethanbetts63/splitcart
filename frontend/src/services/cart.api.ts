import { ApiClient } from './apiClient';
import type { Cart, ApiResponse } from '../types';

/**
 * Fetches the currently active cart.
 */
export const fetchActiveCart = (apiClient: ApiClient): Promise<Cart | null> => {
  return apiClient.get<Cart | null>('/api/carts/active/');
};

/**
 * Syncs the entire cart state with the backend.
 */
export const syncCart = (apiClient: ApiClient, cartToSync: Cart): Promise<Cart> => {
  return apiClient.post<Cart>('/api/carts/sync/', {
    cart_id: cartToSync.id,
    items: cartToSync.items.map((item) => ({
      product_id: typeof item.product === 'object' ? item.product.id : item.product,
      quantity: item.quantity,
      substitutions: (item.substitutions ?? []).map((sub) => ({
        id: sub.id,
        is_approved: sub.is_approved,
        quantity: sub.quantity,
      })),
    })),
  });
};

/**
 * Creates a new, empty cart.
 */
export const createNewCart = (apiClient: ApiClient): Promise<Cart> => {
  return apiClient.post<Cart>('/api/carts/', {});
};

/**
 * Renames a specific cart.
 */
export const renameCart = (
  apiClient: ApiClient,
  cartId: string,
  newName: string,
): Promise<Cart> => {
  return apiClient.post<Cart>('/api/carts/rename/', { cart_id: cartId, new_name: newName });
};

/**
 * Deletes a specific cart.
 */
export const deleteCart = (apiClient: ApiClient, cartId: string): Promise<void> => {
  return apiClient.delete(`/api/carts/${cartId}/`);
};

/**
 * Switches the active cart to the one specified by cartId.
 */
export const switchActiveCart = (apiClient: ApiClient, cartId: string): Promise<Cart> => {
  return apiClient.post<Cart>('/api/carts/switch-active/', { cart_id: cartId });
};

/**
 * Runs optimization on a specific cart.
 */
export const optimizeCart = (apiClient: ApiClient, cartId: string): Promise<ApiResponse> => {
  return apiClient.post<ApiResponse>(`/api/carts/${cartId}/optimize/`, {});
};
