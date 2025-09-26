import React from 'react';
import { Card } from 'react-bootstrap';

const ProductTile = ({ product }) => {
  return (
    <Card style={{ width: '18rem' }}>
      <Card.Img variant="top" src={product.image_url || 'https://via.placeholder.com/150'} />
      <Card.Body>
        <Card.Title>{product.name}</Card.Title>
        <Card.Text>
          $10.00
        </Card.Text>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;