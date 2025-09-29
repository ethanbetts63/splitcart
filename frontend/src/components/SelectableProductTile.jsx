import React, { useState } from 'react';
import { Card } from 'react-bootstrap';

const SelectableProductTile = ({ product, isSelected, onSelect }) => {
  const getCompanyColor = (companyName) => {
    switch (companyName.toLowerCase()) {
      case 'coles': return 'red';
      case 'woolworths': return 'green';
      case 'aldi': return 'blue';
      case 'iga': return 'orange';
      default: return 'black';
    }
  };

  const cardStyle = {
    width: '18rem',
    cursor: 'pointer',
    border: isSelected ? '3px solid green' : '1px solid #ddd',
    boxShadow: isSelected ? '0 0 10px rgba(0, 128, 0, 0.5)' : 'none',
  };

  return (
    <Card style={cardStyle} onClick={() => onSelect(product.id)}>
      <Card.Img variant="top" src={product.image_url || 'https://via.placeholder.com/150'} />
      <Card.Body>
        <Card.Title>{product.name}</Card.Title>
        <Card.Text as="div">
          {product.prices && product.prices.map(priceData => {
            const companyColor = getCompanyColor(priceData.company);
            const companyNameStyle = {
              color: companyColor,
              fontWeight: 'bold',
            };
            const priceValueStyle = {
              color: priceData.is_lowest ? 'green' : 'black',
              fontWeight: priceData.is_lowest ? 'bold' : 'normal',
            };
            return (
              <div key={priceData.company}>
                <span style={companyNameStyle}>{priceData.company}</span>: <span style={priceValueStyle}>${priceData.price_display}</span>
              </div>
            );
          })}
        </Card.Text>
      </Card.Body>
    </Card>
  );
};

export default SelectableProductTile;
