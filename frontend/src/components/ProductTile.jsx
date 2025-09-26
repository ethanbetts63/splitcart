import React, { useState } from 'react';
import { Card, Button, Form, InputGroup } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const ProductTile = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const { addItem } = useShoppingList();

  const handleAdd = () => {
    addItem(product, quantity);
  };

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
        <div className="d-flex justify-content-between align-items-center mt-3">
          <InputGroup style={{ width: '120px' }}>
            <Button variant="outline-secondary" onClick={() => setQuantity(Math.max(1, quantity - 1))}>-</Button>
            <Form.Control value={quantity} readOnly className="text-center" />
            <Button variant="outline-secondary" onClick={() => setQuantity(quantity + 1)}>+</Button>
          </InputGroup>
          <Button variant="primary" onClick={handleAdd}>Add</Button>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;
