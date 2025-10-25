import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import type { Cart, ApiResponse } from '@/types';

// Types

export interface CartContextType {
  currentCart: Cart | null;
  userCarts: Cart[];
  optimizationResult: ApiResponse | null;
  setOptimizationResult: (result: ApiResponse | null) => void;
  cartLoading: boolean;

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

export const CartProvider: React.FC<{ children: React.ReactNode, initialCart: Cart | null }> = ({ children, initialCart }) => {
  const { token, anonymousId, isAuthenticated } = useAuth();
  const [currentCart, setCurrentCart] = useState<Cart | null>(null);
  const [userCarts, setUserCarts] = useState<Cart[]>([]);
  const [optimizationResult, setOptimizationResult] = useState<ApiResponse | null>(null);
  const [cartLoading, setCartLoading] = useState(true);


  useEffect(() => {
    if (initialCart) {
      setCurrentCart(initialCart);
      setCartLoading(false);
    }
  }, [initialCart]);

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
      toast.error('Failed to fetch active cart.');
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
    } catch (error: any) {
        toast.error(error.message);
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
    } catch (error: any) {
        toast.error(error.message);
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
        toast.error('Failed to delete cart.');
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
        toast.error('Failed to switch active cart.');
    }
  };

  const addItem = async (productId: number, quantity: number, product: any) => {
    if (!currentCart) return;

    const tempId = `temp-${Date.now()}`;
    const optimisticItem = {
      id: tempId,
      product: { ...product, id: productId },
      quantity: quantity,
      substitutions: [],
    };

    // Storing the original cart state for potential rollback
    const originalCart = currentCart;

    // Optimistically update the UI
    setCurrentCart(prevCart => {
      if (!prevCart) return null;
      
      const existingItemIndex = prevCart.items.findIndex(item => item.product.id === productId);
      
      if (existingItemIndex > -1) {
        // Item exists, update quantity
        const newItems = [...prevCart.items];
        newItems[existingItemIndex].quantity += quantity;
        return { ...prevCart, items: newItems };
      } else {
        // Item doesn't exist, add it
        return { ...prevCart, items: [...prevCart.items, optimisticItem] };
      }
    });

    try {
      const response = await fetch('/api/carts/active/items/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ product: productId, quantity }),
      });

      if (!response.ok) {
        throw new Error('Failed to add item to cart.');
      }

      // Sync with server state
      await fetchActiveCart();

    } catch (error: any) {
      toast.error('Failed to add item to cart. Please try again.');
      // Revert the optimistic update on failure
      setCurrentCart(originalCart);
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
        const response = await fetch(`/api/carts/active/items/${itemId}/`, {
            method: quantity > 0 ? 'PATCH' : 'DELETE',
            headers: getAuthHeaders(),
            body: quantity > 0 ? JSON.stringify({ quantity }) : undefined,
        });

        if (!response.ok) {
            throw new Error('Failed to update item quantity.');
        }

        // A DELETE request won't return the item, so we can't rely on the response body
        // And a PATCH might not return the full cart. Safest is to refetch.
        await fetchActiveCart();

    } catch (error: any) {
        toast.error('Failed to update item. Please try again.');
        // Revert the optimistic update on failure
        setCurrentCart(originalCart);
    }
  };

  const removeItem = (itemId: string) => {
    // The optimistic logic is now handled by updateItemQuantity
    updateItemQuantity(itemId, 0);
  };

  const updateCartItemSubstitution = async (cartItemId: string, substitutionId: string, isApproved: boolean, quantity: number) => {
    try {
      const response = await fetch(`/api/carts/active/items/${cartItemId}/substitutions/${substitutionId}/`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify({ is_approved: isApproved, quantity: quantity }),
      });
    } catch (error: any) {
      toast.error('Failed to update substitution.');
    }
  };

  const removeCartItemSubstitution = async (cartItemId: string, substitutionId: string) => {
    try {
      const response = await fetch(`/api/carts/active/items/${cartItemId}/substitutions/${substitutionId}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!response.ok) throw new Error('Failed to remove cart item substitution.');
      fetchActiveCart(); // Refresh cart
    } catch (error: any) {
      toast.error('Failed to remove substitution.');
    }
  };

  return (
      <CartContext.Provider value={{
            currentCart, userCarts, optimizationResult, setOptimizationResult, cartLoading,
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