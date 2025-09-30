import React, { createContext, useState, useContext } from 'react';

const ShoppingListContext = createContext();

export const useShoppingList = () => {
  return useContext(ShoppingListContext);
};

export const ShoppingListProvider = ({ children }) => {
  const [items, setItems] = useState([]); // Will be a list of lists: [[item1], [item2, subA, subB]]

  const addItem = (product, quantity) => {
    setItems(prevItems => {
      const slotIndex = prevItems.findIndex(slot => slot[0].product.id === product.id);

      if (slotIndex > -1) {
        // If the product already exists as a primary item, update its quantity
        const newItems = [...prevItems];
        const newSlot = [...newItems[slotIndex]];
        newSlot[0] = { ...newSlot[0], quantity: newSlot[0].quantity + quantity };
        newItems[slotIndex] = newSlot;
        return newItems;
      } else {
        // If it's a new item, add a new slot (an array containing the new item)
        return [...prevItems, [{ product, quantity }]];
      }
    });
  };

  const removeItem = (productId) => {
    // Removes an entire slot based on the primary product's ID
    setItems(prevItems => prevItems.filter(slot => slot[0].product.id !== productId));
  };

  const updateItemQuantity = (productId, newQuantity) => {
    setItems(prevItems =>
      prevItems.map(slot => {
        if (slot[0].product.id === productId) {
          const newSlot = [...slot];
          newSlot[0] = { ...newSlot[0], quantity: newQuantity };
          return newSlot;
        }
        return slot;
      })
    );
  };

  const updateSubstitutionChoices = (originalProductId, selectedProducts) => {
    setItems(prevItems => {
      const newItems = [...prevItems];
      const slotIndex = newItems.findIndex(slot => slot[0].product.id === originalProductId);
  
      if (slotIndex > -1) {
        const originalItem = newItems[slotIndex][0];
        
        // The new slot contains the original item, plus all selected products as substitutes.
        // We map them to the { product, quantity } structure.
        const newSlot = selectedProducts.map(p => ({
          product: p,
          // Preserve quantity for the original item, set to 1 for substitutes
          quantity: p.id === originalProductId ? originalItem.quantity : 1
        }));

        // Ensure the original item is always first in the slot.
        newSlot.sort((a, b) => {
            if (a.product.id === originalProductId) return -1;
            if (b.product.id === originalProductId) return 1;
            return 0;
        });

        newItems[slotIndex] = newSlot;
      }
      return newItems;
    });
  };

  const value = {
    items,
    addItem,
    removeItem,
    updateItemQuantity,
    updateSubstitutionChoices,
  };

  return (
    <ShoppingListContext.Provider value={value}>
      {children}
    </ShoppingListContext.Provider>
  );
};