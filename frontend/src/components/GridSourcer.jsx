import React, { useState, useEffect, useCallback } from 'react';
import ProductGrid from './ProductGrid';
import { Container, Spinner } from 'react-bootstrap';

const GridSourcer = ({ searchTerm, sourceUrl, nearbyStoreIds }) => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState(null);
  const [hasMorePages, setHasMorePages] = useState(false);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  const fetchProducts = useCallback(async (urlToFetch) => {
    setIsError(false);
    setError(null);

    let url = urlToFetch;
    const params = new URLSearchParams();

    // Only append params if it's the initial fetch and not a 'next' page URL
    if (!urlToFetch || urlToFetch === '/api/products/' || urlToFetch === '/api/products/bargains/') {
      if (sourceUrl) {
        url = sourceUrl;
        if (nearbyStoreIds && nearbyStoreIds.length > 0) {
          params.append('store_ids', nearbyStoreIds.join(','));
        }
      } else if (searchTerm) {
        url = '/api/products/';
        params.append('search', searchTerm);
      } else {
        url = '/api/products/';
      }

      if (params.toString()) {
        url += `?${params.toString()}`;
      }
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      
      // Handle both paginated and direct list responses
      const productList = Array.isArray(data) ? data : (data.results || []);
      const next = Array.isArray(data) ? null : data.next;
      const count = Array.isArray(data) ? productList.length : data.count;

      return { productList, next, count };

    } catch (e) {
      setIsError(true);
      setError(e.message);
      return { productList: [], next: null, count: 0 };
    }
  }, [searchTerm, sourceUrl, nearbyStoreIds]);

  // Initial fetch
  useEffect(() => {
    setIsLoading(true);
    setProducts([]);
    setNextPageUrl(null);
    setHasMorePages(false);
    setTotalResults(0);

    fetchProducts(null) // Pass null to indicate initial fetch, not a 'next' page URL
      .then(({ productList, next, count }) => {
        setProducts(productList);
        setNextPageUrl(next);
        setHasMorePages(!!next);
        setTotalResults(count);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [fetchProducts]);

  const onLoadMore = useCallback(async () => {
    if (nextPageUrl && !isLoadingMore) {
      setIsLoadingMore(true);
      fetchProducts(nextPageUrl)
        .then(({ productList, next }) => {
          setProducts(prevProducts => [...prevProducts, ...productList]);
          setNextPageUrl(next);
          setHasMorePages(!!next);
        })
        .finally(() => {
          setIsLoadingMore(false);
        });
    }
  }, [nextPageUrl, isLoadingMore, fetchProducts]);

  if (isLoading) {
    return <Container className="text-center my-5"><Spinner animation="border" /></Container>;
  }

  if (isError) {
    return <Container className="text-center my-5 text-danger">Error: {error}</Container>;
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
      hasMorePages={hasMorePages} 
      isLoadingMore={isLoadingMore}
      title={titleText}
    />
  );
};

export default GridSourcer;
