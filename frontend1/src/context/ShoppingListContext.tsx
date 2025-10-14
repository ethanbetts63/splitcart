import React, { createContext, useContext, useState, ReactNode } from 'react';

// --- Type Definitions ---
type Price = {
  id: number;
  price: string;
  store_id: number;
  is_lowest: boolean;
  image_url?: string;
};

type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: Price[];
};

export interface CartItem {
  product: Product;
  quantity: number;
}

interface ShoppingListContextType {
  items: CartItem[];
  addItem: (product: Product, quantity: number) => void;
  removeItem: (productId: number) => void;
  updateItemQuantity: (productId: number, quantity: number) => void;
  cartTotal: number;
}

// --- Context Creation ---
const ShoppingListContext = createContext<ShoppingListContextType | undefined>(undefined);

// --- Provider Component ---
export const ShoppingListProvider = ({ children }: { children: ReactNode }) => {
  const [items, setItems] = useState<CartItem[]>([]);

  const addItem = (product: Product, quantity: number) => {
    setItems(prevItems => {
      const existingItem = prevItems.find(item => item.product.id === product.id);
      if (existingItem) {
        // If item exists, update its quantity
        return prevItems.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        // If item doesn't exist, add it to the cart
        return [...prevItems, { product, quantity }];
      }
    });
  };

  const removeItem = (productId: number) => {
    setItems(prevItems => prevItems.filter(item => item.product.id !== productId));
  };

  const updateItemQuantity = (productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeItem(productId);
    } else {
      setItems(prevItems =>
        prevItems.map(item =>
          item.product.id === productId ? { ...item, quantity } : item
        )
      );
    }
  };

  const cartTotal = items.reduce((total, item) => total + item.quantity, 0);

  return (
    <ShoppingListContext.Provider value={{ items, addItem, removeItem, updateItemQuantity, cartTotal }}>
      {children}
    </ShoppingListContext.Provider>
  );
};

// --- Custom Hook ---
export const useShoppingList = () => {
  const context = useContext(ShoppingListContext);
  if (context === undefined) {
    throw new Error('useShoppingList must be used within a ShoppingListProvider');
  }
  return context;
};
