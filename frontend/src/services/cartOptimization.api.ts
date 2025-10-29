import type { ApiResponse, ExportData } from '../types';

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

export const emailCartAPI = async (exportData: ExportData, token: string | null): Promise<any> => {
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

export const downloadCartAPI = async (exportData: ExportData): Promise<Blob> => {
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