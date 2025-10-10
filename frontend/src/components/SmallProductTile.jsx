
import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import trolleyIcon from '../assets/shopping_cart.svg';
import QuantityAdjuster from './QuantityAdjuster';
import PriceDisplay from './PriceDisplay';
import './../css/SmallProductTile.css';

const SmallProductTile = ({ item, onRemove, onQuantityChange, showSubstitutes = false }) => {
  const { selections } = useShoppingList();

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = trolleyIcon;
  };

  const itemSelections = selections[item.product.id] || [];
  const substitutes = itemSelections.filter(p => p.id !== item.product.id);

  return (
    <div className="small-product-tile">
      <button onClick={() => onRemove(item.product.id)} className="remove-btn">&times;</button>
      
      <div className="row-1">
        <img src={item.product.image_url || trolleyIcon} onError={handleImageError} alt={item.product.name} className="product-image" />
        <div className="product-details">
          <strong>{item.product.name}</strong>
          <div>
            <small className="text-muted">{item.product.brand}</small>
            <span className="product-size">{item.product.size}</span>
          </div>
        </div>
      </div>

      <div className="row-2">
        <PriceDisplay prices={item.product.prices} variant="trolley" />
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <QuantityAdjuster 
            quantity={item.quantity} 
            onQuantityChange={(newQuantity) => {
              const validatedQuantity = Math.max(1, newQuantity);
              onQuantityChange(item.product.id, validatedQuantity);
            }} 
          />
        </div>
      </div>

      {showSubstitutes && substitutes.length > 0 && (
        <div className="substitutes-container">
          <small className="substitutes-label">Substitutes:</small>
          {substitutes.map(sub => (
            <div key={sub.id} className="substitute-item">
              <small>{sub.name}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SmallProductTile;
