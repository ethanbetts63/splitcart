import React from 'react';
import placeholderImage from '../assets/trolley_v3.webp';

const ProductCardContent = ({ product }) => {
  console.log("ProductCardContent received product:", product); // Debug log

  const getCompanyColor = (companyName) => {
    switch (companyName.toLowerCase()) {
      case 'coles': return 'red';
      case 'woolworths': return 'green';
      case 'aldi': return 'blue';
      case 'iga': return 'orange';
      default: return 'var(--text)';
    }
  };

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
            const companyColor = getCompanyColor(priceData.company);
            const companyNameStyle = {
              color: companyColor,
              fontWeight: 'bold',
            };
            const priceValueStyle = {
              color: priceData.is_lowest ? 'var(--success)' : 'var(--text)',
              fontWeight: priceData.is_lowest ? 'bold' : 'normal',
            };
            return (
              <div key={priceData.company}>
                <span style={companyNameStyle}>{priceData.company}</span>: <span style={priceValueStyle}>${priceData.price_display}</span>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default ProductCardContent;
