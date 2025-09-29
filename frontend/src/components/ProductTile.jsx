import React, { useState } from 'react';
import { Card, Button, Form, InputGroup } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import ProductCardContent from './ProductCardContent';

const ProductTile = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const { items, addItem, removeItem } = useShoppingList();

  const isInCart = items.some(item => item.product.id === product.id);

  const handleAdd = () => {
    addItem(product, quantity);
  };

  const handleRemove = () => {
    removeItem(product.id);
  };

  return (
    <Card style={{ width: '18rem' }}>
      <ProductCardContent product={product} />
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mt-3">
          {isInCart ? (
            <Button variant="danger" onClick={handleRemove}>Remove</Button>
          ) : (
            <>
              <InputGroup style={{ width: '120px' }}>
                <Button variant="outline-secondary" onClick={() => setQuantity(Math.max(1, quantity - 1))}>-</Button>
                <Form.Control value={quantity} readOnly className="text-center" />
                <Button variant="outline-secondary" onClick={() => setQuantity(quantity + 1)}>+</Button>
              </InputGroup>
              <Button variant="primary" onClick={handleAdd}>Add</Button>
            </>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;