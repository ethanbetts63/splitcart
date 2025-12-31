import React, { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import type { Cart, ApiResponse } from '../types';
import { createApiClient, ApiError } from '../services/apiClient';

// Types

export interface CartContextType {
  currentCart: Cart | null;
  userCarts: Cart[];
  optimizationResult: ApiResponse | null;
  setOptimizationResult: (result: ApiResponse | null) => void;
  cartLoading: boolean;
  isFetchingSubstitutions: boolean; // New state for substitution loading

  fetchActiveCart: () => void;
  loadCart: (cartId: string) => void;
  createNewCart: () => void;
  renameCart: (cartId: string, newName: string) => void;
  deleteCart: (cartId: string) => void;
  addItem: (productId: number, quantity: number, product: any) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
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
      const data = await apiClient.get<Cart | null>('/api/carts/active/');
      setCurrentCart(data);
      return data;
    } catch (error: any) {
      if (error instanceof ApiError && error.statusCode === 404) {
        // A 404 is acceptable here, means no active cart.
        setCurrentCart(null);
      } else {
        toast.error('Failed to fetch active cart.');
        setCurrentCart(null); // Ensure cart is null on error
      }
      return null;
    } finally {
      setCartLoading(false);
    }
  }, [apiClient]);

  // Fetch initial data
  useEffect(() => {
    if (!isAuthLoading) {
      fetchActiveCart();
    }
  }, [isAuthLoading, fetchActiveCart]);

  const fetchUserCarts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await apiClient.get<{ results: Cart[] }>('/api/carts/');
      setUserCarts(data.results || []);
    } catch (error: any) {
      console.error(error.message);
      toast.error('Failed to fetch user carts.');
    }
  }, [apiClient, isAuthenticated]);

  const loadCart = async (cartId: string) => {
    // This will become the active cart on the backend
    await switchActiveCart(cartId);
  };

  const createNewCart = async () => {
    try {
        const newCart = await apiClient.post<Cart>('/api/carts/', {});
        setCurrentCart(newCart);
    } catch (error: any) {
        toast.error(error.message || 'Failed to create new cart.');
    }
  };

  const renameCart = async (cartId: string, newName: string) => {
    try {
        const updatedCart = await apiClient.post<Cart>('/api/cart/rename/', { cart_id: cartId, new_name: newName });
        setCurrentCart(updatedCart);
    } catch (error: any) {
        toast.error(error.message || 'Failed to rename cart.');
    }
  };

  const deleteCart = async (cartId: string) => {
    try {
        await apiClient.delete(`/api/carts/${cartId}/`);
        // After deleting, fetch the new active cart
        fetchActiveCart();
        fetchUserCarts();
    } catch (error: any) {
        toast.error(error.message || 'Failed to delete cart.');
    }
  };

  const switchActiveCart = async (cartId: string) => {
    try {
        const newActiveCart = await apiClient.post<Cart>('/api/cart/switch-active/', { cart_id: cartId });
        setCurrentCart(newActiveCart);
        fetchUserCarts();
    } catch (error: any) {
        toast.error(error.message || 'Failed to switch active cart.');
    }
  };

  const addItem = async (productId: number, quantity: number, product: any) => {
    setIsFetchingSubstitutions(true);
    
    // Use a variable to hold the cart state we'll be working with.
    let workingCart = currentCart;

    // If there's no cart, fetch/create it first.
    if (!workingCart) {
      try {
        workingCart = await fetchActiveCart();
        if (!workingCart) {
          toast.error('Could not retrieve or create a cart.');
          setIsFetchingSubstitutions(false);
          return;
        }
      } catch (error) {
          toast.error('Failed to get cart. Please try again.');
          setIsFetchingSubstitutions(false);
          return;
      }
    }
    
    // Now we're sure workingCart is not null.
    const cartId = workingCart.id;
    const originalCartState = workingCart; // Save state for rollback.

    // --- Optimistic Update ---
    const tempId = `temp-${Date.now()}`;
    const existingItemIndex = workingCart.items.findIndex(item => item.product.id === productId);
    let optimisticallyUpdatedCart;

    if (existingItemIndex > -1) {
      // Item exists, update quantity
      const newItems = [...workingCart.items];
      newItems[existingItemIndex].quantity += quantity;
      optimisticallyUpdatedCart = { ...workingCart, items: newItems };
    } else {
      // Item doesn't exist, add it
      const optimisticItem = {
        id: tempId,
        product: { ...product, id: productId },
        quantity: quantity,
        substitutions: [],
      };
      optimisticallyUpdatedCart = { ...workingCart, items: [...workingCart.items, optimisticItem] };
    }

    setCurrentCart(optimisticallyUpdatedCart);

    try {
      // Use the correct URL with the cart ID
      const realCartItem = await apiClient.post<any>(`/api/carts/${cartId}/items/`, { product: productId, quantity });

      // Replace the temporary item with the real one from the server.
      setCurrentCart(prevCart => {
        if (!prevCart) return null;
        return {
          ...prevCart,
          items: prevCart.items.map(item => 
            item.id === tempId ? realCartItem : item
          ),
        };
      });

    } catch (error: any) {
      toast.error(error.message || 'Failed to add item to cart. Please try again.');
      // Revert on failure
      setCurrentCart(originalCartState);
    } finally {
      setIsFetchingSubstitutions(false);
    }
  };

  const updateItemQuantity = async (itemId: string, quantity: number) => {
    if (!currentCart) return;

    const originalCart = { ...currentCart, items: [...currentCart.items.map(i => ({...i}))] }; // Deep copy for rollback
    let itemExists = false;

    const newCart = {
        ...currentCart,
        items: currentCart.items.map(item => {
            if (item.id === itemId) {
                itemExists = true;
                return { ...item, quantity };
            }
            return item;
        }).filter(item => item.quantity > 0) // Also handle item removal if quantity is 0 or less
    };

    if (!itemExists) return; // Don't do anything if the item isn't in the cart

    setCurrentCart(newCart);

            try {
                if (quantity > 0) {
                    await apiClient.patch(`/api/carts/active/items/${itemId}/`, { quantity });
                } else {
                    await apiClient.delete(`/api/carts/active/items/${itemId}/`);
                }
            } catch (error: any) {
                toast.error(error.message || 'Failed to update item. Please try again.');
                // Revert the optimistic update on failure
                setCurrentCart(originalCart);
            }  };

  const removeItem = (itemId: string) => {
    // The optimistic logic is now handled by updateItemQuantity
    updateItemQuantity(itemId, 0);
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
            addItem, updateItemQuantity, removeItem, updateCartItemSubstitution, removeCartItemSubstitution
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