import React from 'react';
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

const ProductCardContent = ({ product }) => {
  console.log("ProductCardContent received product:", product); // Debug log

  if (!product) {
    console.log("ProductCardContent received null or undefined product."); // Debug log
    return null; // Don't render if no product
  }

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = placeholderImage;
  };

  return (
    <>
      <img 
        src={product.image_url || placeholderImage} 
        onError={handleImageError}
        style={{ width: '100%', objectFit: 'cover' }}
      />
      <div style={{ padding: '1rem' }}>
        <h4>{product.name}</h4>
        {product.brand_name && <h5 style={{ color: 'var(--text-muted)' }}>{product.brand_name}</h5>}
        {product.size && <p style={{ color: 'var(--text-muted)' }}>Size: {product.size}</p>}
        <div>
          {product.prices && product.prices.map(priceData => {
            const priceValueStyle = {
              color: priceData.is_lowest ? 'var(--success)' : 'var(--text)',
              fontWeight: priceData.is_lowest ? 'bold' : 'normal',
            };
            return (
              <div key={priceData.company} style={{ display: 'flex', alignItems: 'center', marginBottom: '0.25rem' }}>
                <img src={companyLogos[priceData.company]} alt={`${priceData.company} logo`} height="20" style={{ marginRight: '0.5rem' }} />
                <span style={priceValueStyle}>${priceData.price_display}</span>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default ProductCardContent;