import React from 'react';
import ProductTile from './ProductTile';

const ProductGrid = ({ products, onLoadMore, hasMorePages, isLoadingMore, title, nearbyStoreIds }) => {

  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(18rem, 1fr))',
    gap: '1rem',
    justifyItems: 'center'
  };

  const mediaQueryStyles = `
    @media (max-width: 768px) {
      .grid-container {
        grid-template-columns: repeat(auto-fill, minmax(13.5rem, 1fr));
      }
    }
  `;

  return (
    <div>
      <style>{mediaQueryStyles}</style>
      {title && <h5 style={{ fontSize: '1.2rem', marginTop: '0.1rem', marginBottom: '1rem' }}>{title}</h5>}
      <div className="grid-container" style={gridStyles}>
        {products.length > 0 ? (
          products.map((product) => (
            <div key={product.id}>
              <ProductTile product={product} nearbyStoreIds={nearbyStoreIds} />
            </div>
          ))
        ) : (
          <div style={{ textAlign: 'center', gridColumn: '1 / -1' }}>No products found.</div>
        )}
      </div>

      {hasMorePages && (
        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <button onClick={onLoadMore} disabled={isLoadingMore}>
            {isLoadingMore ? 'Loading...' : 'Load More'}
          </button>
        </div>
      )}
    </div>
  );
};

export default ProductGrid;