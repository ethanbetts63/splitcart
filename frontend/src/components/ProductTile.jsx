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
    border: `1px solid ${existingItem ? 'var(--primary)' : 'var(--border)'}`,
    borderRadius: '8px',
    width: '18rem',
    backgroundColor: '#FFFFFF',
    boxShadow: existingItem ? '0 0 5px var(--primary)' : 'none',
    transition: 'border 0.2s, boxShadow 0.2s'
  };

  return (
        <div style={tileStyle}>
      <ProductCardContent product={product} />
      <div style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
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