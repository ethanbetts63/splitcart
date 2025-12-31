import React, { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import type { Cart, ApiResponse } from '../types';
import { createApiClient, ApiError } from '../services/apiClient';
import { debounce } from '../lib/utils';
import * as cartApi from '../services/cart.api';

// Types

export interface CartContextType {
  currentCart: Cart | null;
  userCarts: Cart[];
  optimizationResult: ApiResponse | null;
  setOptimizationResult: (result: ApiResponse | null) => void;
  cartLoading: boolean;
  isFetchingSubstitutions: boolean; // New state for substitution loading

  fetchActiveCart: () => Promise<Cart | null>;
  loadCart: (cartId: string) => void;
  createNewCart: () => void;
  renameCart: (cartId: string, newName: string) => void;
  deleteCart: (cartId: string) => void;
  addItem: (productId: number, quantity: number, product: any) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  optimizeCurrentCart: () => Promise<ApiResponse | null>;
  updateCartItemSubstitution: (cartItemId: string, substitutionId: string, isApproved: boolean, quantity: number) => void;
  removeCartItemSubstitution: (cartItemId: string, substitutionId: string) => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, anonymousId, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [currentCart, setCurrentCart] = useState<Cart | null>(null);
  const [userCarts, setUserCarts] = useState<Cart[]>([]);
  const [optimizationResult, setOptimizationResult] = useState<ApiResponse | null>(null);
  const [cartLoading, setCartLoading] = useState(true);
  const [isFetchingSubstitutions, setIsFetchingSubstitutions] = useState(false); // Initialize new state
  
  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);
  
  const fetchActiveCart = useCallback(async (): Promise<Cart | null> => {
    setCartLoading(true);
    try {
      const data = await cartApi.fetchActiveCart(apiClient);
      setCurrentCart(data);
      return data;
    } catch (error: any) {
      if (error instanceof ApiError && error.statusCode === 404) {
        setCurrentCart(null);
      } else {
        toast.error('Failed to fetch active cart.');
        setCurrentCart(null);
      }
      return null;
    } finally {
      setCartLoading(false);
    }
  }, [apiClient]);

  // Debounced sync function
  const debouncedSync = useCallback(
    debounce(async (cartToSync: Cart) => {
      try {
        const updatedCart = await cartApi.syncCart(apiClient, cartToSync);
        setCurrentCart(updatedCart);
      } catch (error) {
        toast.error("Failed to sync cart with server. Attempting to restore.");
        fetchActiveCart();
      } finally {
        setIsFetchingSubstitutions(false);
      }
    }, 1500),
    [apiClient, fetchActiveCart]
  );


  // Fetch initial data
  useEffect(() => {
    if (!isAuthLoading) {
      fetchActiveCart();
    }
  }, [isAuthLoading, fetchActiveCart]);

  const fetchUserCarts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      // This is not a cart-specific call, could be moved to a user.api.ts or similar
      const data = await apiClient.get<{ results: Cart[] }>('/api/carts/');
      setUserCarts(data.results || []);
    } catch (error: any) {
      console.error(error.message);
      toast.error('Failed to fetch user carts.');
    }
  }, [apiClient, isAuthenticated]);

  const loadCart = async (cartId: string) => {
    await switchActiveCart(cartId);
  };

  const createNewCart = async () => {
    try {
        const newCart = await cartApi.createNewCart(apiClient);
        setCurrentCart(newCart);
    } catch (error: any) {
        toast.error(error.message || 'Failed to create new cart.');
    }
  };

  const renameCart = async (cartId: string, newName: string) => {
    try {
        const updatedCart = await cartApi.renameCart(apiClient, cartId, newName);
        setCurrentCart(updatedCart);
    } catch (error: any) {
        toast.error(error.message || 'Failed to rename cart.');
    }
  };

  const deleteCart = async (cartId: string) => {
    try {
        await cartApi.deleteCart(apiClient, cartId);
        fetchActiveCart();
        fetchUserCarts();
    } catch (error: any) {
        toast.error(error.message || 'Failed to delete cart.');
    }
  };

  const switchActiveCart = async (cartId: string) => {
    try {
        const newActiveCart = await cartApi.switchActiveCart(apiClient, cartId);
        setCurrentCart(newActiveCart);
        fetchUserCarts();
    } catch (error: any) {
        toast.error(error.message || 'Failed to switch active cart.');
    }
  };

  const addItem = async (productId: number, quantity: number, product: any) => {
    setIsFetchingSubstitutions(true);
    
    let workingCart = currentCart;
    if (!workingCart) {
      workingCart = await fetchActiveCart();
      if (!workingCart) {
        toast.error('Could not retrieve or create a cart.');
        setIsFetchingSubstitutions(false);
        return;
      }
    }
    
    // Optimistically update UI
    const existingItemIndex = workingCart.items.findIndex(item => item.product.id === productId);
    let optimisticallyUpdatedCart: Cart;

    if (existingItemIndex > -1) {
      const newItems = [...workingCart.items];
      newItems[existingItemIndex].quantity += quantity;
      optimisticallyUpdatedCart = { ...workingCart, items: newItems };
    } else {
      const optimisticItem = {
        id: `temp-${Date.now()}`,
        product: { ...product, id: productId },
        quantity: quantity,
        substitutions: [],
      };
      optimisticallyUpdatedCart = { ...workingCart, items: [...workingCart.items, optimisticItem] };
    }

    setCurrentCart(optimisticallyUpdatedCart);
    debouncedSync(optimisticallyUpdatedCart);
  };

  const updateItemQuantity = (itemId: string, quantity: number) => {
    if (!currentCart) return;
    setIsFetchingSubstitutions(true);

    const optimisticallyUpdatedCart = {
        ...currentCart,
        items: currentCart.items
            .map(item => (item.id === itemId ? { ...item, quantity } : item))
            .filter(item => item.quantity > 0)
    };

    setCurrentCart(optimisticallyUpdatedCart);
    debouncedSync(optimisticallyUpdatedCart);
  };

  const removeItem = (itemId: string) => {
    updateItemQuantity(itemId, 0);
  };

  const optimizeCurrentCart = async (): Promise<ApiResponse | null> => {
    if (!currentCart) {
      toast.error("No active cart to optimize.");
      return null;
    }
    try {
      const results = await cartApi.optimizeCart(apiClient, currentCart.id);
      setOptimizationResult(results);
      return results;
    } catch (error: any) {
      toast.error(error.message || "Failed to run optimization.");
      return null;
    }
  };

  const updateCartItemSubstitution = async (cartItemId: string, substitutionId: string, isApproved: boolean, quantity: number) => {
    if (!currentCart) return;

    const originalCart = JSON.parse(JSON.stringify(currentCart)); // Deep copy for rollback

    // Optimistically update the UI
    setCurrentCart(prevCart => {
      if (!prevCart) return null;

      const updatedItems = prevCart.items.map(item => {
        if (item.id === cartItemId) {
          const updatedSubstitutions = item.substitutions
            ? item.substitutions.map(sub => 
                sub.id === substitutionId ? { ...sub, is_approved: isApproved, quantity: quantity } : sub
              )
            : [];
          return { ...item, substitutions: updatedSubstitutions };
        }
        return item;
      });

      return { ...prevCart, items: updatedItems };
    });

    try {
      await apiClient.patch(`/api/cart-items/${cartItemId}/substitutions/${substitutionId}/`, { is_approved: isApproved, quantity: quantity });
    } catch (error: any) {
      toast.error(error.message || 'Failed to update substitution. Please try again.');
      // Revert the optimistic update on failure
      setCurrentCart(originalCart);
    }
  };

  const removeCartItemSubstitution = async (cartItemId: string, substitutionId: string) => {
    try {
      await apiClient.delete(`/api/cart-items/${cartItemId}/substitutions/${substitutionId}/`);
      fetchActiveCart(); // Refresh cart
    } catch (error: any) {
      toast.error(error.message || 'Failed to remove substitution.');
    }
  };

  return (
      <CartContext.Provider value={{
            currentCart, userCarts, optimizationResult, setOptimizationResult, cartLoading, isFetchingSubstitutions,
            fetchActiveCart, loadCart, createNewCart, renameCart, deleteCart,
            addItem, updateItemQuantity, removeItem, optimizeCurrentCart,
            updateCartItemSubstitution, removeCartItemSubstitution
        }}>
          {children}
        </CartContext.Provider>  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};