import React, { useState, useEffect, useCallback } from 'react';
import ProductGrid from './ProductGrid';

// Helper to convert absolute URL from API to a relative path
const getRelativePath = (url) => {
  if (!url) return null;
  try {
    const urlObject = new URL(url);
    return urlObject.pathname + urlObject.search;
  } catch (error) {
    // If it's already a relative path or invalid, return as is
    return url;
  }
};

const GridSourcer = ({ searchTerm, sourceUrl, nearbyStoreIds }) => {
  console.log('GridSourcer props:', { searchTerm, sourceUrl, nearbyStoreIds });
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState(null);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  const fetchProducts = useCallback(async (urlToFetch, isInitialLoad) => {
    setIsError(false);
    setError(null);

    let url;
    if (isInitialLoad) {
      const params = new URLSearchParams();
      if (sourceUrl) {
        url = sourceUrl;
        if (nearbyStoreIds && nearbyStoreIds.length > 0) {
          params.append('store_ids', nearbyStoreIds.map(store => store.id).join(','));
        }
      } else {
        url = '/api/products/';
        if (searchTerm) {
          params.append('search', searchTerm);
        }
      }
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
    } else {
      url = urlToFetch;
    }

    if (!url) return;

    console.log('Fetching products from:', url);

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Received data:', data);
      
      const productList = data.results || [];
      const nextUrl = getRelativePath(data.next); // Convert to relative path
      const count = data.count !== undefined ? data.count : products.length + productList.length;

      if (isInitialLoad) {
        setProducts(productList);
        setTotalResults(count);
      } else {
        setProducts(prev => [...prev, ...productList]);
      }
      setNextPageUrl(nextUrl);

    } catch (e) {
      console.error('Fetch error:', e);
      setIsError(true);
      setError(e.message);
    }
  }, [searchTerm, sourceUrl, nearbyStoreIds, products.length]);

  // Initial fetch effect
  useEffect(() => {
    console.log('GridSourcer useEffect triggered');
    setIsLoading(true);
    setProducts([]);
    setNextPageUrl(null);
    setTotalResults(0);
    
    fetchProducts(null, true).finally(() => {
      setIsLoading(false);
    });
  }, [searchTerm, sourceUrl, nearbyStoreIds]); // Dependency array simplified

  const onLoadMore = useCallback(() => {
    if (nextPageUrl && !isLoadingMore) {
      setIsLoadingMore(true);
      fetchProducts(nextPageUrl, false).finally(() => {
        setIsLoadingMore(false);
      });
    }
  }, [nextPageUrl, isLoadingMore, fetchProducts]);

  if (isLoading) {
    return <div style={{ textAlign: 'center', margin: '2rem 0' }}>Loading...</div>;
  }

  if (isError) {
    return <div style={{ textAlign: 'center', margin: '2rem 0', color: 'red' }}>Error: {error}</div>;
  }

  let titleText = "";
  if (searchTerm) {
    titleText = `Found ${totalResults} results for "${searchTerm}"`;
  } else if (sourceUrl === '/api/products/bargains/') {
    titleText = `Bargain Finds! (${totalResults} results)`;
  } else if (sourceUrl === '/api/products/') {
    titleText = `All Products (${totalResults} results)`;
  }

  return (
    <ProductGrid 
      products={products} 
      onLoadMore={onLoadMore} 
      hasMorePages={!!nextPageUrl} 
      isLoadingMore={isLoadingMore}
      title={titleText}
      nearbyStoreIds={nearbyStoreIds}
    />
  );
};

export default GridSourcer;
