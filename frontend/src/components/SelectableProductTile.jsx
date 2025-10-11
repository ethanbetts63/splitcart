import React, { useState, useEffect } from 'react';
import '../css/SelectableProductTile.css';
import placeholderImage from '../assets/shopping_cart.svg';
import QuantityAdjuster from './QuantityAdjuster';
import PriceDisplay from './PriceDisplay';

const SelectableProductTile = ({ product, isSelected, onSelect, onQuantityChange, initialQuantity = 1, is_original }) => {
  const [quantity, setQuantity] = useState(initialQuantity);

  useEffect(() => {
    setQuantity(initialQuantity);
  }, [initialQuantity]);

  const handleQuantityChange = (newQuantity) => {
    const validatedQuantity = Math.max(1, newQuantity);
    setQuantity(validatedQuantity);
    if (onQuantityChange) {
      onQuantityChange(product.id, validatedQuantity);
    }
  };

  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = placeholderImage;
  };

  const prices = product.prices || [];

  const cardStyle = {
    border: isSelected ? '3px solid var(--success)' : '1px solid var(--border-color)',
    boxShadow: isSelected ? '0 0 10px var(--success)' : 'none',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    height: '100%',
    background: isSelected ? 'linear-gradient(to bottom, #d4edda, white)' : 'white',
  };

  return (
    <div className="product-card" style={cardStyle}>
      <div>
        <div style={{ position: 'relative' }}>
          <img
            src={product.image_url || placeholderImage}
            onError={handleImageError}
            alt={product.name}
          />
          {(is_original || product.level_description) && (
            <span style={{
              position: 'absolute',
              top: '15px',
              right: '15px',
              backgroundColor: 'white',
              color: 'black',
              padding: '0.2rem 0.4rem',
              borderRadius: '8px',
              fontSize: '0.8rem',
              border: '1px solid var(--colorp2)',
              zIndex: 1,
              fontFamily: 'var(--font-numeric)'
            }}>
              {is_original ? 'Original Product' : product.level_description}
            </span>
          )}
        </div>
        <div className="product-card-content">
          <h3>{product.name}</h3>
          <p>
            {product.brand_name && `${product.brand_name} `}
            {product.size && `(${product.size})`}
          </p>
          
          <PriceDisplay prices={prices} variant="product-tile" />
        </div>
      </div>

      <div className="actions-container" style={{ marginTop: '0.5rem' }}>
        <div className="action-item">
          <QuantityAdjuster 
            quantity={quantity} 
            onQuantityChange={handleQuantityChange} 
          />
        </div>
        <div className="action-item">
          <button 
            onClick={() => onSelect(product.id)} 
            className={`btn ${isSelected ? 'red-btn' : 'green-btn'}`}
          >
            {isSelected ? 'Remove' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SelectableProductTile;
