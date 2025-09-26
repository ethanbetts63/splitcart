import React from 'react';
import { Card } from 'react-bootstrap';

const ProductTile = ({ product }) => {
  return (
    <Card style={{ width: '18rem' }}>
      <Card.Img variant="top" src={product.image_url || 'https://via.placeholder.com/150'} />
      <Card.Body>
        <Card.Title>{product.name}</Card.Title>
        <Card.Text as="div">
          {product.prices && product.prices.map(price => (
            <div key={price.store}>{price.store}: ${price.price}</div>
          ))}
        </Card.Text>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;