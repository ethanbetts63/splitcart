import { getAuthHeaders } from './getAuthHeaders';
import type { Cart, CartItem, Product } from '@/types';

const BASE_URL = '/api';

// --- Cart API ---

export const getActiveCartAPI = async (token: string | null, anonymousId: string | null): Promise<Cart> => {
    const response = await fetch(`${BASE_URL}/carts/active/`, {
        headers: getAuthHeaders(token, anonymousId),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch active cart');
    }
    return response.json();
};

export const createCartAPI = async (name: string, token: string | null, anonymousId: string | null): Promise<Cart> => {
    const response = await fetch(`${BASE_URL}/carts/`, {
        method: 'POST',
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify({ name }),
    });
    if (!response.ok) {
        throw new Error('Failed to create cart');
    }
    return response.json();
};

export const switchActiveCartAPI = async (cartId: string, token: string): Promise<Cart> => {
    const response = await fetch(`${BASE_URL}/carts/switch-active/`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ cart_id: cartId }),
    });
    if (!response.ok) {
        throw new Error('Failed to switch active cart');
    }
    return response.json();
};

// --- Cart Item API ---

export const addCartItemAPI = async (productId: number, quantity: number, token: string | null, anonymousId: string | null): Promise<CartItem> => {
    const response = await fetch(`${BASE_URL}/carts/active/items/`, {
        method: 'POST',
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (!response.ok) {
        throw new Error('Failed to add item to cart');
    }
    return response.json();
};

export const updateCartItemAPI = async (itemId: number, quantity: number, token: string | null, anonymousId: string | null): Promise<CartItem> => {
    const response = await fetch(`${BASE_URL}/carts/active/items/${itemId}/`, {
        method: 'PUT',
        headers: getAuthHeaders(token, anonymousId),
        body: JSON.stringify({ quantity }),
    });
    if (!response.ok) {
        throw new Error('Failed to update item in cart');
    }
    return response.json();
};

export const removeCartItemAPI = async (itemId: number, token: string | null, anonymousId: string | null): Promise<void> => {
    const response = await fetch(`${BASE_URL}/carts/active/items/${itemId}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(token, anonymousId),
    });
    if (!response.ok) {
        throw new Error('Failed to remove item from cart');
    }
};
