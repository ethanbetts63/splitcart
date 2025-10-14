import React from 'react';
import { Link } from 'react-router-dom';
import ProductTile from './ProductTile';
import SkeletonProductCard from './SkeletonProductCard'; // Import skeleton
import '../css/HorizontalProductScroller.css';

const HorizontalProductScroller = ({ title, products, seeMoreLink = "#", isLoading }) => {
  if (!isLoading && (!products || products.length === 0)) {
    return null; // Don't render anything if not loading and no products
  }

  return (
    <div className="horizontal-scroller-container" style={{ marginBottom: '1rem' }}>
      <div className="scroller-header">
        <h2 style={{ fontFamily: 'var(--ff-primary)', color: 'var(--color-p)' }}>{title}</h2>
        {seeMoreLink && <Link to={seeMoreLink} className="see-more-link">See More</Link>}
      </div>
      <div className="scroller-content">
        {isLoading ? (
          Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="scroller-item">
              <SkeletonProductCard />
            </div>
          ))
        ) : (
          products.map(product => (
            <div key={product.id} className="scroller-item">
              <ProductTile product={product} />
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default HorizontalProductScroller;
