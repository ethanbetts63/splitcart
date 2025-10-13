import React, { createContext, useState, useContext, useCallback } from 'react';

const ProductCacheContext = createContext();

export const useProductCache = () => {
  return useContext(ProductCacheContext);
};

export const ProductCacheProvider = ({ children }) => {
  const [cache, setCache] = useState({});

  const fetchAndCacheProducts = useCallback(async (url) => {
    if (cache[url]) {
      console.log('Cache hit for:', url);
      return cache[url];
    }

    console.log('Cache miss for:', url, 'Fetching from network...');
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setCache(prevCache => ({ ...prevCache, [url]: data }));
      return data;
    } catch (error) {
      console.error(`Error fetching products for ${url}:`, error);
      throw error; // Re-throw the error to be handled by the caller
    }
  }, [cache]);

  const value = {
    fetchAndCacheProducts,
  };

  return (
    <ProductCacheContext.Provider value={value}>
      {children}
    </ProductCacheContext.Provider>
  );
};
