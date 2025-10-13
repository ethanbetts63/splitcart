import React, { useState, useEffect } from 'react';
import HorizontalProductScroller from './HorizontalProductScroller';
import { useProductCache } from '../context/ProductCacheContext';

const SearchSourcer = ({ title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, isLocationLoaded }) => {
  console.log('SearchSourcer props:', { title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, isLocationLoaded });
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const { fetchAndCacheProducts } = useProductCache();

  useEffect(() => {
    console.log('SearchSourcer useEffect triggered for:', title);
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

      console.log('Fetching products for scroller:', url);

      try {
        const data = await fetchAndCacheProducts(url);
        if (isMounted) {
          console.log('Received data for scroller:', title, data);
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

    getProducts();

    return () => {
      isMounted = false;
    };
  }, [title, searchTerm, sourceUrl, nearbyStoreIds, seeMoreLink, fetchAndCacheProducts]);

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