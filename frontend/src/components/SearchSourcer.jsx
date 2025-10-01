import React, { useState, useEffect } from 'react';
import HorizontalProductScroller from './HorizontalProductScroller';

const SearchSourcer = ({ title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, onLoadComplete }) => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    
    let url = '';
    if (sourceUrl) {
      url = sourceUrl;
      if (nearbyStoreIds && nearbyStoreIds.length > 0) {
        const params = new URLSearchParams();
        params.append('store_ids', nearbyStoreIds.join(','));
        url = `${url}?${params.toString()}`;
      }
    } else if (searchTerm) {
      url = `/api/products/?search=${encodeURIComponent(searchTerm)}`;
    } else {
      url = '/api/products/';
    }

    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (isMounted) {
          // Handle both paginated and direct list responses
          const productList = Array.isArray(data) ? data : (data.results || []);
          setProducts(productList.slice(0, 20));
          setError(null);
        }
      })
      .catch(error => {
        if (isMounted) {
          console.error(`Error fetching products for '${title}':`, error);
          setError(error.message);
          setProducts([]);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
          if (onLoadComplete) {
            onLoadComplete();
          }
        }
      });

    return () => {
      isMounted = false;
    };
  }, [title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, onLoadComplete]);

  // The HorizontalProductScroller now handles the loading and empty states internally.
  return (
    <HorizontalProductScroller
      title={title}
      products={products}
      seeMoreLink={seeMoreLink}
      isLoading={isLoading}
    />
  );
};

export default SearchSourcer;