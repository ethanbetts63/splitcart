import React, { useState, useEffect } from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import '../css/ProductTile.css';
import placeholderImage from '../assets/trolley_v3.png';
import QuantityAdjuster from './QuantityAdjuster';
import PriceDisplay from './PriceDisplay';

// Logos - moved from ProductCardContent
import aldiLogo from '../assets/ALDI_logo.svg';
import colesLogo from '../assets/coles_logo.webp';
import igaLogo from '../assets/iga_logo.webp';
import woolworthsLogo from '../assets/woolworths_logo.webp';

const companyLogos = {
    'Aldi': aldiLogo,
    'Coles': colesLogo,
    'Iga': igaLogo,
    'Woolworths': woolworthsLogo,
};

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

  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = placeholderImage;
  };

  const handleAdd = () => {
    addItem(product, quantity, nearbyStoreIds);
  };

  const handleRemove = () => {
    removeItem(product.id);
  };

  const prices = product.prices || [];

  const priceContainerStyle = {
    display: 'grid',
    gridTemplateColumns: prices.length === 1 ? '1fr' : 'repeat(2, 1fr)',
    gap: '0.05rem',
    marginTop: '0.5rem',
    justifyItems: prices.length === 1 ? 'center' : 'start',
  };

  return (
    <div className="product-card">
      <div style={{ position: 'relative' }}>
        <img
          src={product.image_url || placeholderImage}
          onError={handleImageError}
          alt={product.name}
        />
        {product.size && (
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
            fontFamily: 'Arial, sans-serif'
          }}>
            {product.size}
          </span>
        )}
      </div>
      <div className="product-card-content">
        <h3>{product.name}</h3>
        <p>
          {product.brand_name && `${product.brand_name} `}
        </p>
        
        <PriceDisplay prices={prices} variant="product-tile" />

        <div className="actions-container">
          <div className="action-item" />
          <div className="action-item">
            <QuantityAdjuster 
              className="action-element"
              quantity={quantity} 
              onQuantityChange={handleQuantityChange} 
            />
          </div>
          <div className="action-item">
            {existingItem ? (
              <button onClick={handleRemove} className="btn remove-btn action-element">Remove</button>
            ) : (
              <button onClick={handleAdd} className="btn action-element">Add</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductTile;
