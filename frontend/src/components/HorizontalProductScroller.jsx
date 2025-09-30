import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ProductTile from './ProductTile';
import './HorizontalProductScroller.css';

const HorizontalProductScroller = ({ title, onLoadComplete }) => {
  const [products, setProducts] = useState([]);

  useEffect(() => {
    let isMounted = true;
    fetch('/api/products/')
      .then(response => response.json())
      .then(data => {
        if (isMounted && data && data.results) {
          setProducts(data.results.slice(0, 20));
        }
      })
      .catch(error => {
        console.error(`Error fetching products for scroller '${title}':`, error);
      })
      .finally(() => {
        if (isMounted && onLoadComplete) {
          onLoadComplete();
        }
      });

    return () => {
      isMounted = false;
    };
  }, [title, onLoadComplete]);

  if (products.length === 0) {
    return null; // Don't render anything until products are loaded
  }

  return (
    <div className="horizontal-scroller-container">
      <div className="scroller-header">
        <h2>{title}</h2>
        <Link to="#" className="see-more-link">See More</Link>
      </div>
      <div className="scroller-content">
        {products.map(product => (
          <div key={product.id} className="scroller-item">
            <ProductTile product={product} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default HorizontalProductScroller;
