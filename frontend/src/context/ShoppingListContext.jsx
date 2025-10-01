import React, { createContext, useState, useContext, useCallback, useEffect, useRef } from 'react';

const ShoppingListContext = createContext();

export const useShoppingList = () => {
  return useContext(ShoppingListContext);
};

export const ShoppingListProvider = ({ children }) => {
  const [items, setItems] = useState([]);
  const [substitutes, setSubstitutes] = useState({});
  const [userLocation, setUserLocation] = useState(null);
  const [nearbyStoreIds, setNearbyStoreIds] = useState([]);
  const [selections, setSelections] = useState({}); // { originalProductId: [product, product, ...] }
  const prevStoreIdsRef = useRef();

  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    }
  }, []);

  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      setUserLocation(JSON.parse(savedLocation));
    }
  }, []);

  const fetchSubstitutes = useCallback(async (product, storeIds) => {
    if (!product || !storeIds || storeIds.length === 0) {
      return;
    }
    try {
      const url = `/api/products/${product.id}/substitutes/?store_ids=${storeIds.join(',')}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const subs = await response.json();
      setSubstitutes(prevSubs => ({ ...prevSubs, [product.id]: subs }));
    } catch (error) {
      console.error(`Error fetching substitutes for product ${product.id}:`, error);
      setSubstitutes(prevSubs => ({ ...prevSubs, [product.id]: [] }));
    }
  }, []);

  useEffect(() => {
    const fetchStoreIds = async () => {
      if (userLocation && userLocation.postcode && userLocation.radius) {
        try {
          const response = await fetch(`/api/stores/nearby/?postcode=${userLocation.postcode}&radius=${userLocation.radius}`);
          if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
          const data = await response.json();
          setNearbyStoreIds(data);
        } catch (error) {
          console.error("Error fetching nearby store IDs:", error);
          setNearbyStoreIds([]);
        }
      }
    };
    fetchStoreIds();
  }, [userLocation]);

  // Effect to re-fetch substitutes when location changes
  useEffect(() => {
    const hasStoreIdsChanged = JSON.stringify(prevStoreIdsRef.current) !== JSON.stringify(nearbyStoreIds);

    if (hasStoreIdsChanged && nearbyStoreIds.length > 0 && items.length > 0) {
      items.forEach(item => fetchSubstitutes(item.product, nearbyStoreIds));
    }

    // Update the ref for the next render
    prevStoreIdsRef.current = nearbyStoreIds;
  }, [nearbyStoreIds, items, fetchSubstitutes]);

  const addItem = useCallback((product, quantity) => {
    setItems(prevItems => {
      const existingItem = prevItems.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevItems.map(item =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + quantity } : item
        );
      } else {
        return [...prevItems, { product, quantity }];
      }
    });
    if (nearbyStoreIds.length > 0) {
      fetchSubstitutes(product, nearbyStoreIds);
    }
  }, [nearbyStoreIds, fetchSubstitutes]);

  const removeItem = (productId) => {
    setItems(prevItems => prevItems.filter(item => item.product.id !== productId));
    setSubstitutes(prevSubs => {
      const newSubs = { ...prevSubs };
      delete newSubs[productId];
      return newSubs;
    });
  };

  const updateItemQuantity = (productId, newQuantity) => {
    setItems(prevItems =>
      prevItems.map(item =>
        item.product.id === productId ? { ...item, quantity: newQuantity } : item
      )
    );
  };

  const updateSubstitutionChoices = (originalProductId, selectedProducts) => {
    setSelections(prev => ({ ...prev, [originalProductId]: selectedProducts }));
  };

  const value = {
    items,
    substitutes,
    selections, // Export selections
    addItem,
    removeItem,
    updateItemQuantity,
    updateSubstitutionChoices, // Export the real function
    userLocation,
    setUserLocation,
    nearbyStoreIds,
  };

  return (
    <ShoppingListContext.Provider value={value}>
      {children}
    </ShoppingListContext.Provider>
  );
};