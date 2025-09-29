import React, { createContext, useState, useContext } from 'react';

const ShoppingListContext = createContext();

export const useShoppingList = () => {
  return useContext(ShoppingListContext);
};

export const ShoppingListProvider = ({ children }) => {
  const [items, setItems] = useState([]);

  const addItem = (product, quantity) => {
    setItems(prevItems => {
      const existingItem = prevItems.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevItems.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        return [...prevItems, { product, quantity }];
      }
    });
  };

  const removeItem = (productId) => {
    setItems(prevItems => prevItems.filter(item => item.product.id !== productId));
  };

  const value = {
    items,
    addItem,
    removeItem,
  };

  return (
    <ShoppingListContext.Provider value={value}>
      {children}
    </ShoppingListContext.Provider>
  );
};