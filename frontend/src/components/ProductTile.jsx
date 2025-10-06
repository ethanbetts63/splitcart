import React, { useState, useEffect } from 'react';
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

  const tileStyle = {
    borderRadius: '8px',
    width: '18rem',
    backgroundColor: '#FFFFFF',
    boxShadow: existingItem ? '0 0 10px var(--primary)' : 'none',
    transition: 'boxShadow 0.2s',
    height: '32rem', // Fixed height
    display: 'flex',
    flexDirection: 'column'
  };

  const contentWrapperStyle = {
    flex: 1, // Make content grow
    overflow: 'hidden' // Hide overflow
  };

  return (
        <div style={tileStyle}>
      <div style={contentWrapperStyle}>
        <ProductCardContent product={product} />
      </div>
      <div style={{ padding: '0.5rem 1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <button onClick={() => handleQuantityChange(quantity - 1)}>-</button>
            <input value={quantity} readOnly style={{ width: '40px', textAlign: 'center' }} />
            <button onClick={() => handleQuantityChange(quantity + 1)}>+</button>
          </div>
          {existingItem ? (
            <button onClick={handleRemove} style={{ marginLeft: '0.5rem', backgroundColor: 'var(--danger)', color: 'white' }}>Remove</button>
          ) : (
            <button onClick={handleAdd} style={{ backgroundColor: 'var(--primary)', color: 'white' }}>Add</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductTile;