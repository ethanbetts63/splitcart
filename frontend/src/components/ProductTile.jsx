import React, { useState, useEffect } from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import '../css/ProductTile.css';
import placeholderImage from '../assets/trolley_v3.png';

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
      <img
        src={product.image_url || placeholderImage}
        onError={handleImageError}
        alt={product.name}
      />
      <div className="product-card-content">
        <h3>{product.name}</h3>
        <p>
          {product.brand_name && `${product.brand_name} `}
          {product.size && `(${product.size})`}
        </p>
        
        {/* Prices */}
        <div style={priceContainerStyle}>
          {prices.map(priceData => (
            <div key={priceData.company} style={{ display: 'flex', alignItems: 'center' }}>
              <img src={companyLogos[priceData.company]} alt={`${priceData.company} logo`} style={{ height: '20px', marginRight: '0.25rem' }} />
              <span style={{ color: priceData.is_lowest ? 'var(--success)' : 'var(--text)' }}>
                ${priceData.price_display}
              </span>
            </div>
          ))}
        </div>

        {existingItem ? (
          <button onClick={handleRemove} className="btn">Remove</button>
        ) : (
          <button onClick={handleAdd} className="btn">Add to Cart</button>
        )}
      </div>
    </div>
  );
};

export default ProductTile;
