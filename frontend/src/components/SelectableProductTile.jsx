import React from 'react';
import '../css/ProductTile.css'; // Reuse the same CSS
import placeholderImage from '../assets/trolley_v3.png';

// Logos
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

const SelectableProductTile = ({ product, isSelected, onSelect }) => {
  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = placeholderImage;
  };

  const prices = product.prices || [];

  const priceContainerStyle = {
    display: 'grid',
    gridTemplateColumns: prices.length === 1 ? '1fr' : 'repeat(2, 1fr)',
    gap: '0.05rem',
    marginTop: '0.5rem',
    justifyItems: prices.length === 1 ? 'center' : 'start',
  };

  const cardStyle = {
    border: isSelected ? '3px solid var(--success)' : 'none',
    boxShadow: isSelected ? '0 0 10px var(--success)' : 'none',
    cursor: 'pointer',
  };

  return (
    <div className="product-card" style={cardStyle} onClick={() => onSelect(product.id)}>
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
      </div>
    </div>
  );
};

export default SelectableProductTile;