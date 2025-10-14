import React, { useState, useEffect, useCallback } from 'react';
import ProductGrid from './ProductGrid';
import { Product } from '@/types'; // Import shared type

// Type for the API response, using the shared Product type
type ApiResponse = {
  count: number;
  next: string | null;
  results: Product[];
};

interface GridSourcerProps {
  searchTerm: string | null;
  sourceUrl: string | null;
}

const GridSourcer: React.FC<GridSourcerProps> = ({ searchTerm, sourceUrl }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextPageUrl, setNextPageUrl] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  const fetchProducts = useCallback(async (urlToFetch: string, isInitialLoad: boolean) => {
    setIsError(false);
    setError(null);

    try {
      const response = await fetch(urlToFetch);
      if (!response.ok) {
        // Try to parse error response, but fall back to status text
        let errorMessage = `Failed to fetch: ${response.statusText}`;
        try {
            const errData = await response.json();
            errorMessage = errData.detail || errData.error || errorMessage;
        } catch (e) {
            // Response was not JSON, stick with the status text
        }
        throw new Error(errorMessage);
      }
      const data: ApiResponse = await response.json();
      
      const productList = data.results || [];
      const nextUrl = data.next; 
      const count = data.count;

      if (isInitialLoad) {
        setProducts(productList);
        setTotalResults(count);
      } else {
        setProducts(prev => [...prev, ...productList]);
      }
      setNextPageUrl(nextUrl);

    } catch (e: any) {
      setIsError(true);
      setError(e.message);
    }
  }, []);

  // Effect for the initial data fetch
  useEffect(() => {
    let url = '';
    const params = new URLSearchParams();

    if (sourceUrl) {
      url = sourceUrl;
    } else if (searchTerm) {
      url = '/api/products/';
      params.append('search', searchTerm);
    } else {
      // Don't fetch if there's no search term or source URL
      setIsLoading(false);
      setProducts([]);
      setTotalResults(0);
      return;
    }

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    setIsLoading(true);
    setProducts([]);
    setNextPageUrl(null);
    setTotalResults(0);
    
    fetchProducts(url, true).finally(() => {
      setIsLoading(false);
    });
  }, [searchTerm, sourceUrl, fetchProducts]);

  const onLoadMore = useCallback(() => {
    if (nextPageUrl && !isLoadingMore) {
      setIsLoadingMore(true);
      fetchProducts(nextPageUrl, false).finally(() => {
        setIsLoadingMore(false);
      });
    }
  }, [nextPageUrl, isLoadingMore, fetchProducts]);

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error}</div>;
  }

  let titleText = "";
  if (searchTerm) {
    titleText = `Found ${totalResults} results for "${searchTerm}"`;
  } else if (sourceUrl) {
    // Basic title for sourceUrl, can be improved
    titleText = `Showing ${totalResults} products`;
  } else if (products.length === 0) {
    titleText = "Please enter a search to begin.";
  }

  return (
    <ProductGrid 
      products={products} 
      onLoadMore={onLoadMore} 
      hasMorePages={!!nextPageUrl} 
      isLoadingMore={isLoadingMore}
      title={titleText}
    />
  );
};

export default GridSourcer;