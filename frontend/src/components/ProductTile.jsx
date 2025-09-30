import React, { useState, useEffect } from 'react';
import { Card, Button, Form, InputGroup } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';
import ProductCardContent from './ProductCardContent';

const ProductTile = ({ product }) => {
  const { items, addItem, removeItem, updateItemQuantity } = useShoppingList();
  
  // Find the slot (the inner array) that contains the product.
  const existingItemSlot = items.find(slot => slot[0].product.id === product.id);
  // The actual item is the first element of the slot.
  const existingItem = existingItemSlot ? existingItemSlot[0] : null;

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