import { ApiClient } from './apiClient';
import type { Cart, ApiResponse, ExportData } from '../types';

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
        items: cartToSync.items.map(item => ({
            // Ensure we are only sending primitive types if product is a full object
            product_id: typeof item.product === 'object' ? item.product.id : item.product,
            quantity: item.quantity,
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
 * Note: Corrected URL from '/api/cart/rename/' to '/api/carts/rename/'.
 */
export const renameCart = (apiClient: ApiClient, cartId: string, newName: string): Promise<Cart> => {
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

/**
 * Emails the cart/shopping list to the user.
 * Note: This uses raw fetch as it requires specific header handling not in the generic apiClient.
 */
export const emailCart = async (exportData: ExportData, token: string | null): Promise<any> => {
  if (!token) {
    throw new Error("Authentication token is required to email the shopping list.");
  }

  const response = await fetch('/api/cart/email-list/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify(exportData),
  });

  const resData = await response.json();

  if (!response.ok) {
    throw new Error(resData.error || `Server returned an unexpected error (${response.status}).`);
  }

  return resData;
};

/**
 * Generates and downloads a PDF of the cart/shopping list.
 * Note: This uses raw fetch to handle the blob response for the PDF file.
 */
export const downloadCart = async (exportData: ExportData): Promise<Blob> => {
  const response = await fetch('/api/cart/download-list/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exportData),
  });

  if (!response.ok) {
    const contentType = response.headers.get("content-type");
    let errorMessage = 'Failed to generate PDF.';
    if (contentType && contentType.indexOf("application/json") !== -1) {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
    } else {
        errorMessage = `Server returned an unexpected error (${response.status}).`;
    }
    throw new Error(errorMessage);
  }

  const blob = await response.blob();
  return blob;
};
