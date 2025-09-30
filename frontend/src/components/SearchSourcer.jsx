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

  if (isLoading) {
    // Optional: render a loading state placeholder
    return (
      <div className="horizontal-scroller-container">
        <div className="scroller-header">
          <h2>{title}</h2>
        </div>
        <div className="scroller-content" style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    // Optional: render an error state
    return (
        <div className="horizontal-scroller-container">
          <div className="scroller-header">
            <h2>{title}</h2>
          </div>
          <div className="scroller-content" style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p>Error loading products.</p>
        </div>
      </div>
    );
  }

  // Render the dumb scroller with the fetched products
  return <HorizontalProductScroller title={title} products={products} seeMoreLink={seeMoreLink} />;
};

export default SearchSourcer;