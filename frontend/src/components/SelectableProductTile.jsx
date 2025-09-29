import React from 'react';
import { Card } from 'react-bootstrap';
import ProductCardContent from './ProductCardContent';

const SelectableProductTile = ({ product, isSelected, onSelect }) => {
  const cardStyle = {
    cursor: 'pointer',
    border: isSelected ? '3px solid green' : '1px solid #ddd',
    boxShadow: isSelected ? '0 0 10px rgba(0, 128, 0, 0.5)' : 'none',
  };

  return (
    <Card style={cardStyle} onClick={() => onSelect(product.id)}>
      <ProductCardContent product={product} />
    </Card>
  );
};

export default SelectableProductTile;
