import React from 'react';
import '../css/ProductTile.css';
import '../css/PrimaryProductTile.css';
import logoSymbol from '../assets/splitcart_symbol_v6.png';
import PriceDisplay from './PriceDisplay';
import AddToCartButton from './AddToCartButton';

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
  const handleImageError = (e) => {
    e.target.onerror = null;
    e.target.src = logoSymbol;
  };

  const prices = product.prices || [];

  return (
    <div className="product-card">
      <div style={{ position: 'relative' }}>
        <img
          src={product.image_url || logoSymbol}
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
            fontFamily: 'var(--font-numeric)'
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
          <AddToCartButton product={product} nearbyStoreIds={nearbyStoreIds} />
        </div>
      </div>
    </div>
  );
};

export default ProductTile;
