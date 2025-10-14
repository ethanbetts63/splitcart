import React, { useState, useEffect } from 'react';
import HorizontalProductScroller from './HorizontalProductScroller';

const BargainSourcer = ({ title, nearbyStoreIds, onLoadComplete }) => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    if (!nearbyStoreIds || nearbyStoreIds.length === 0) {
      setIsLoading(false);
      // Don't fetch if there are no nearby stores selected
      return;
    }

    const params = new URLSearchParams();
    params.append('store_ids', nearbyStoreIds.join(','));
    const url = `/api/products/bargains/?${params.toString()}`;

    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (isMounted) {
          // The API returns a list of products directly
          setProducts(data || []);
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
  }, [title, nearbyStoreIds, onLoadComplete]);

  return <HorizontalProductScroller title={title} products={products} isLoading={isLoading} />;
};

export default BargainSourcer;
