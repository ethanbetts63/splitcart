import React from 'react';
import { Link } from 'react-router-dom';
import ProductTile from './ProductTile';
import SkeletonProductCard from './SkeletonProductCard'; // Import skeleton
import './HorizontalProductScroller.css';

const HorizontalProductScroller = ({ title, products, seeMoreLink = "#", isLoading }) => {
  return (
    <div className="horizontal-scroller-container">
      <div className="scroller-header">
        <h2>{title}</h2>
        {seeMoreLink && <Link to={seeMoreLink} className="see-more-link">See More</Link>}
      </div>
      <div className="scroller-content">
        {isLoading ? (
          Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="scroller-item">
              <SkeletonProductCard />
            </div>
          ))
        ) : products && products.length > 0 ? (
          products.map(product => (
            <div key={product.id} className="scroller-item">
              <ProductTile product={product} />
            </div>
          ))
        ) : (
          <div className="scroller-empty-message">
            <p>No products found for this category.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HorizontalProductScroller;
