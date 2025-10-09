import React, { useState, useEffect } from 'react';
import HorizontalProductScroller from './HorizontalProductScroller';
import { useProductCache } from '../context/ProductCacheContext';

const SearchSourcer = ({ title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, isLocationLoaded }) => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { fetchAndCacheProducts } = useProductCache();

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);

    const getProducts = async () => {
      let url = '';
      if (sourceUrl) {
        url = sourceUrl;
        if (nearbyStoreIds && nearbyStoreIds.length > 0) {
          const params = new URLSearchParams();
          params.append('store_ids', nearbyStoreIds.map(store => store.id).join(','));
          url = `${url}?${params.toString()}`;
        }
      } else if (searchTerm) {
        url = `/api/products/?search=${encodeURIComponent(searchTerm)}`;
      } else {
        url = '/api/products/';
      }

      try {
        const data = await fetchAndCacheProducts(url);
        if (isMounted) {
          const productList = Array.isArray(data) ? data : (data.results || []);
          setProducts(productList.slice(0, 20));
          setError(null);
        }
      } catch (error) {
        if (isMounted) {
          console.error(`Error fetching products for '${title}':`, error);
          setError(error.message);
          setProducts([]);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    if (isLocationLoaded) {
      getProducts();
    } else {
      setIsLoading(true);
    }

    return () => {
      isMounted = false;
    };
  }, [title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, isLocationLoaded, fetchAndCacheProducts]);

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