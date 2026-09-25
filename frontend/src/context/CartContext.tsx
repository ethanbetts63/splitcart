import React, { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';
import type { Cart, ApiResponse, Product } from '../types';
import type { CartContextType } from '../types/CartContextType';
import { createApiClient, ApiError, apiErrorMessage } from '../services/apiClient';
import { debounce } from '../lib/debounce';
import * as cartApi from '../services/cart.api';

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, anonymousId, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [currentCart, setCurrentCart] = useState<Cart | null>(null);
  const [userCarts, setUserCarts] = useState<Cart[]>([]);
  const [optimizationResult, setOptimizationResult] = useState<ApiResponse | null>(null);
  const [cartLoading, setCartLoading] = useState(true);
  const [isCartSyncing, setIsFetchingSubstitutions] = useState(false); // Initialize new state

  const apiClient = useMemo(() => createApiClient(token, anonymousId), [token, anonymousId]);

  /**
   * The fetch itself, without asserting the loading flag.
   *
   * Split out from `fetchActiveCart` for the mount effect below: `cartLoading`
   * already starts true, so the first load has nothing to announce, and a
   * `setCartLoading(true)` reached synchronously from an effect body is a
   * cascading render (react-hooks/set-state-in-effect).
   */
  const loadActiveCart = useCallback(
    (): Promise<Cart | null> =>
      cartApi
        .fetchActiveCart(apiClient)
        .then((data) => {
          setCurrentCart(data);
          return data;
        })
        .catch((error: unknown) => {
          // A 404 is the ordinary "this visitor has no cart yet" answer, not
          // a failure worth a toast.
          if (!(error instanceof ApiError && error.statusCode === 404)) {
            toast.error('Failed to fetch active cart.');
          }
          setCurrentCart(null);
          return null;
        })
        .finally(() => setCartLoading(false)),
    [apiClient],
  );

  const fetchActiveCart = useCallback(async (): Promise<Cart | null> => {
    setCartLoading(true);
    return loadActiveCart();
  }, [loadActiveCart]);

  // Debounced sync function
  const debouncedSync = useMemo(
    () =>
      debounce(async (cartToSync: Cart) => {
        try {
          const updatedCart = await cartApi.syncCart(apiClient, cartToSync);

          setCurrentCart((prevCart) => {
            // If the cart has not changed since this sync was initiated,
            // it's safe to update with the server's response.
            if (JSON.stringify(prevCart) === JSON.stringify(cartToSync)) {
              return updatedCart;
            } else {
              // The local cart has changed. The server's response is outdated.
              // Discard the server response and keep the current local state.
              // A new sync will already be in the debounce queue from the user's latest action.
              return prevCart;
            }
          });
        } catch {
          toast.error('Failed to sync cart with server. Attempting to restore.');
          void fetchActiveCart();
        } finally {
          setIsFetchingSubstitutions(false);
        }
      }, 1500),
    [apiClient, fetchActiveCart],
  );

  // Fetch initial data
  useEffect(() => {
    if (!isAuthLoading) {
      void loadActiveCart();
    }
  }, [isAuthLoading, loadActiveCart]);

  const fetchUserCarts = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      // This is not a cart-specific call, could be moved to a user.api.ts or similar
      const data = await apiClient.get<{ results: Cart[] }>('/api/carts/');
      setUserCarts(data.results || []);
    } catch (error) {
      console.error(apiErrorMessage(error, 'Failed to fetch user carts.'));
      toast.error('Failed to fetch user carts.');
    }
  }, [apiClient, isAuthenticated]);

  const switchActiveCart = async (cartId: string) => {
    try {
      const newActiveCart = await cartApi.switchActiveCart(apiClient, cartId);
      setCurrentCart(newActiveCart);
      void fetchUserCarts();
    } catch (error) {
      toast.error(apiErrorMessage(error, 'Failed to switch active cart.'));
    }
  };

  const loadCart = async (cartId: string) => {
    await switchActiveCart(cartId);
  };

  const createNewCart = async () => {
    try {
      const newCart = await cartApi.createNewCart(apiClient);
      setCurrentCart(newCart);
    } catch (error) {
      toast.error(apiErrorMessage(error, 'Failed to create new cart.'));
    }
  };

  const renameCart = async (cartId: string, newName: string) => {
    try {
      const updatedCart = await cartApi.renameCart(apiClient, cartId, newName);
      setCurrentCart(updatedCart);
    } catch (error) {
      toast.error(apiErrorMessage(error, 'Failed to rename cart.'));
    }
  };

  const deleteCart = async (cartId: string) => {
    try {
      await cartApi.deleteCart(apiClient, cartId);
      void fetchActiveCart();
      void fetchUserCarts();
    } catch (error) {
      toast.error(apiErrorMessage(error, 'Failed to delete cart.'));
    }
  };

  const addItem = async (productId: number, quantity: number, product: Product) => {
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
    const existingItemIndex = workingCart.items.findIndex((item) => item.product.id === productId);
    let optimisticallyUpdatedCart: Cart;

    if (existingItemIndex > -1) {
      const newItems = workingCart.items.map((item, index) =>
        index === existingItemIndex ? { ...item, quantity: item.quantity + quantity } : item,
      );
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
        .map((item) => (item.id === itemId ? { ...item, quantity } : item))
        .filter((item) => item.quantity > 0),
    };

    setCurrentCart(optimisticallyUpdatedCart);
    debouncedSync(optimisticallyUpdatedCart);
  };

  const removeItem = (itemId: string) => {
    updateItemQuantity(itemId, 0);
  };

  const optimizeCurrentCart = async (): Promise<ApiResponse | null> => {
    if (!currentCart) {
      toast.error('No active cart to optimize.');
      return null;
    }
    try {
      const results = await cartApi.optimizeCart(apiClient, currentCart.id);
      setOptimizationResult(results);
      return results;
    } catch (error) {
      toast.error(apiErrorMessage(error, 'Failed to run optimization.'));
      return null;
    }
  };

  const updateCartItemSubstitution = (
    cartItemId: string,
    substitutionId: string,
    isApproved: boolean,
    quantity: number,
  ) => {
    if (!currentCart) return;

    const updatedCart = {
      ...currentCart,
      items: currentCart.items.map((item) => {
        if (item.id !== cartItemId) return item;
        return {
          ...item,
          substitutions: (item.substitutions ?? []).map((sub) =>
            sub.id === substitutionId ? { ...sub, is_approved: isApproved, quantity } : sub,
          ),
        };
      }),
    };

    setCurrentCart(updatedCart);
    debouncedSync(updatedCart);
  };

  return (
    <CartContext.Provider
      value={{
        currentCart,
        userCarts,
        optimizationResult,
        setOptimizationResult,
        cartLoading,
        isCartSyncing,
        fetchActiveCart,
        loadCart,
        createNewCart,
        renameCart,
        deleteCart,
        addItem,
        updateItemQuantity,
        removeItem,
        optimizeCurrentCart,
        updateCartItemSubstitution,
      }}
    >
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
