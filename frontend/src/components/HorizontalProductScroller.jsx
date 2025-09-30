import React from 'react';
import { Link } from 'react-router-dom';
import ProductTile from './ProductTile';
import './HorizontalProductScroller.css';

const HorizontalProductScroller = ({ title, products }) => {
  if (!products || products.length === 0) {
    return null; // Don't render anything if there are no products
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
