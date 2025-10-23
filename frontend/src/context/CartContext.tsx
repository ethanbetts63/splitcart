import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import {
    getActiveCartAPI,
    addCartItemAPI,
    updateCartItemAPI,
    removeCartItemAPI,
} from '@/services/cartApi';
import type { Cart, CartItem, Product } from '@/types';

interface CartContextType {
    cart: Cart | null;
    items: CartItem[];
    loading: boolean;
    error: string | null;
    addItem: (product: Product, quantity: number) => Promise<void>;
    updateItemQuantity: (itemId: number, quantity: number) => Promise<void>;
    removeItem: (itemId: number) => Promise<void>;
    clearCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider = ({ children }: { children: ReactNode }) => {
    const { token, anonymousId } = useAuth();
    const [cart, setCart] = useState<Cart | null>(null);
    const [items, setItems] = useState<CartItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchCart = useCallback(async () => {
        if (!token && !anonymousId) return;
        setLoading(true);
        try {
            const activeCart = await getActiveCartAPI(token, anonymousId);
            setCart(activeCart);
            setItems(activeCart.items || []);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [token, anonymousId]);

    useEffect(() => {
        fetchCart();
    }, [fetchCart]);

    const addItem = async (product: Product, quantity: number) => {
        const existingItem = items.find(item => item.product.id === product.id);
        if (existingItem) {
            await updateItemQuantity(existingItem.id, existingItem.quantity + quantity);
        } else {
            try {
                const newItem = await addCartItemAPI(product.id, quantity, token, anonymousId);
                setItems(prevItems => [...prevItems, newItem]);
            } catch (err: any) {
                setError(err.message);
            }
        }
    };

    const updateItemQuantity = async (itemId: number, quantity: number) => {
        if (quantity <= 0) {
            await removeItem(itemId);
        } else {
            try {
                const updatedItem = await updateCartItemAPI(itemId, quantity, token, anonymousId);
                setItems(prevItems => prevItems.map(item => item.id === itemId ? updatedItem : item));
            } catch (err: any) {
                setError(err.message);
            }
        }
    };

    const removeItem = async (itemId: number) => {
        try {
            await removeCartItemAPI(itemId, token, anonymousId);
            setItems(prevItems => prevItems.filter(item => item.id !== itemId));
        } catch (err: any) {
            setError(err.message);
        }
    };

    const clearCart = async () => {
        // This would require a new API endpoint, for now, we remove items one by one
        try {
            await Promise.all(items.map(item => removeCartItemAPI(item.id, token, anonymousId)));
            setItems([]);
        } catch (err: any) {
            setError(err.message);
        }
    };

    const contextValue = {
        cart,
        items,
        loading,
        error,
        addItem,
        updateItemQuantity,
        removeItem,
        clearCart,
    };

    return (
        <CartContext.Provider value={contextValue}>
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
