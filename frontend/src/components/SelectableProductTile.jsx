import React from 'react';
import ProductCardContent from './ProductCardContent';

const SelectableProductTile = ({ product, isSelected, onSelect }) => {
  const cardStyle = {
    cursor: 'pointer',
    border: isSelected ? '3px solid var(--success)' : '1px solid var(--border)',
    boxShadow: isSelected ? '0 0 10px var(--success)' : 'none',
    borderRadius: '8px'
  };

  return (
    <div style={cardStyle} onClick={() => onSelect(product.id)}>
      <ProductCardContent product={product} />
    </div>
  );
};

export default SelectableProductTile;
