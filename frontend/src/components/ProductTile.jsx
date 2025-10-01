import React, { useState, useEffect } from 'react';
import { Card, Button, Form, InputGroup } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import ProductCardContent from './ProductCardContent';

const ProductTile = ({ product, nearbyStoreIds }) => {
  const { items, addItem, removeItem, updateItemQuantity } = useShoppingList();
  
  const existingItem = items.find(item => item.product.id === product.id);

  const [quantity, setQuantity] = useState(existingItem ? existingItem.quantity : 1);

  useEffect(() => {
    setQuantity(existingItem ? existingItem.quantity : 1);
  }, [existingItem]);

  const handleQuantityChange = (newQuantity) => {
    const validatedQuantity = Math.max(1, newQuantity);
    setQuantity(validatedQuantity);
    if (existingItem) {
      updateItemQuantity(product.id, validatedQuantity);
    }
  };

  const handleAdd = () => {
    addItem(product, quantity, nearbyStoreIds);
  };

  const handleRemove = () => {
    removeItem(product.id);
  };

  return (
    <Card style={{ width: '18rem' }}>
      <ProductCardContent product={product} />
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center mt-3">
          <InputGroup style={{ width: '120px' }}>
            <Button variant="outline-secondary" onClick={() => handleQuantityChange(quantity - 1)}>-</Button>
            <Form.Control value={quantity} readOnly className="text-center" />
            <Button variant="outline-secondary" onClick={() => handleQuantityChange(quantity + 1)}>+</Button>
          </InputGroup>
          {existingItem ? (
            <Button variant="danger" onClick={handleRemove} className="ms-2">Remove</Button>
          ) : (
            <Button variant="primary" onClick={handleAdd}>Add</Button>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default ProductTile;