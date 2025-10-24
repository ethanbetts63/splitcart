import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import type { Product, Cart, CartItem, ApiResponse } from '@/types';

// Types

export interface CartContextType {
  currentCart: Cart | null;
  userCarts: Cart[];
  optimizationResult: ApiResponse | null;
  setOptimizationResult: (result: ApiResponse | null) => void;
  cartLoading: boolean;
  cartError: string | null;
  fetchActiveCart: () => void;
  loadCart: (cartId: string) => void;
  createNewCart: () => void;
  renameCart: (cartId: string, newName: string) => void;
  deleteCart: (cartId: string) => void;
  addItem: (productId: number, quantity: number) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, anonymousId, isAuthenticated } = useAuth();
  const [currentCart, setCurrentCart] = useState<Cart | null>(null);
  const [userCarts, setUserCarts] = useState<Cart[]>([]);
  const [optimizationResult, setOptimizationResult] = useState<ApiResponse | null>(null);
  const [cartLoading, setCartLoading] = useState(true);
  const [cartError, setCartError] = useState<string | null>(null);

  const getAuthHeaders = useCallback(() => {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    if (isAuthenticated && token) {
      headers['Authorization'] = `Token ${token}`;
    } else if (anonymousId) {
      headers['X-Anonymous-ID'] = anonymousId;
    }
    return headers;
  }, [token, anonymousId, isAuthenticated]);

  const fetchActiveCart = useCallback(async () => {
    setCartLoading(true);
    try {
      const response = await fetch('/api/carts/active/', { headers: getAuthHeaders() });
      if (!response.ok) throw new Error('Failed to fetch active cart.');
      const data = await response.json();
      setCurrentCart(data);
    } catch (error: any) {
      setCartError(error.message);
    } finally {
      setCartLoading(false);
    }
  }, [getAuthHeaders]);

  const fetchUserCarts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const response = await fetch('/api/carts/', { headers: getAuthHeaders() });
      if (!response.ok) throw new Error('Failed to fetch user carts.');
      const data = await response.json();
      setUserCarts(data.results || []);
    } catch (error: any) {
      console.error(error.message);
    }
  }, [getAuthHeaders, isAuthenticated]);

  useEffect(() => {
    if (token || anonymousId) {
      fetchActiveCart();
      if (isAuthenticated) {
        fetchUserCarts();
      }
    }
  }, [token, anonymousId, isAuthenticated, fetchActiveCart, fetchUserCarts]);

  const loadCart = async (cartId: string) => {
    // This will become the active cart on the backend
    await switchActiveCart(cartId);
  };

  const createNewCart = async () => {
    try {
        const response = await fetch('/api/carts/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({}),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create new cart.');
        }
        const newCart = await response.json();
        setCurrentCart(newCart);
        fetchUserCarts(); // Refresh the list of user carts
        setCartError(null);
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  const renameCart = async (cartId: string, newName: string) => {
    try {
        const response = await fetch('/api/carts/rename/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ cart_id: cartId, new_name: newName }),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to rename cart.');
        }
        const updatedCart = await response.json();
        setCurrentCart(updatedCart);
        fetchUserCarts();
        setCartError(null); // Clear any previous errors
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  const deleteCart = async (cartId: string) => {
    try {
        const response = await fetch(`/api/carts/${cartId}/`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to delete cart.');
        // After deleting, fetch the new active cart
        fetchActiveCart();
        fetchUserCarts();
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  const switchActiveCart = async (cartId: string) => {
    try {
        const response = await fetch('/api/carts/switch-active/', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ cart_id: cartId }),
        });
        if (!response.ok) throw new Error('Failed to switch active cart.');
        const newActiveCart = await response.json();
        setCurrentCart(newActiveCart);
        fetchUserCarts();
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  const addItem = async (productId: number, quantity: number) => {
    try {
      // Add item to cart
      const addItemResponse = await fetch('/api/carts/active/items/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ product: productId, quantity }),
      });
      if (!addItemResponse.ok) throw new Error('Failed to add item to cart.');
      await fetchActiveCart(); // Refresh cart to show the new item

    } catch (error: any) {
      setCartError(error.message);
    }
  };

  const updateItemQuantity = async (itemId: string, quantity: number) => {
    try {
        const response = await fetch(`/api/carts/active/items/${itemId}/`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify({ quantity }),
        });
        if (!response.ok) throw new Error('Failed to update item quantity.');
        fetchActiveCart(); // Refresh cart
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  const removeItem = async (itemId: string) => {
    try {
        const response = await fetch(`/api/carts/active/items/${itemId}/`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('Failed to remove item from cart.');
        fetchActiveCart(); // Refresh cart
    } catch (error: any) {
        setCartError(error.message);
    }
  };

  return (
    <CartContext.Provider value={{ 
        currentCart, userCarts, potentialSubstitutes, optimizationResult, setOptimizationResult, cartLoading, cartError,
        fetchActiveCart, loadCart, createNewCart, renameCart, deleteCart,
        addItem, updateItemQuantity, removeItem
    }}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};