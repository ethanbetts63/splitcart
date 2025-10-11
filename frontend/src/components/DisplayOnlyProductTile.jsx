
import React from 'react';
import placeholderImage from '../assets/splitcart_symbol_v6.png';
import './../css/SmallProductTile.css'; // Reuse the same CSS for a consistent look

const DisplayOnlyProductTile = ({ item }) => {

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = placeholderImage;
  };

  return (
    <div className="small-product-tile" style={{ marginBottom: '0.25rem' }}>
      <div className="row-1">
        <img src={item.image_url || placeholderImage} onError={handleImageError} alt={item.name} className="product-image" />
        <div className="product-details">
          <strong>{item.name}</strong>
          <div>
            <small className="text-muted">{item.brand}</small>
            <span className="product-size">{item.size}</span>
          </div>
        </div>
      </div>

      <div className="row-2">
        <div>
            <span style={{ fontFamily: 'var(--font-numeric)' }}>${item.price.toFixed(2)}</span>
        </div>
        <div>
            <span style={{ fontFamily: 'var(--font-numeric)' }}>Qty: {item.quantity}</span>
        </div>
      </div>
    </div>
  );
};

export default DisplayOnlyProductTile;
