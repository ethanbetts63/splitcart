
import React from 'react';
import trolleyIcon from '../assets/shopping_cart.svg';
import './../css/SmallProductTile.css'; // Reuse the same CSS for a consistent look

const DisplayOnlyProductTile = ({ item }) => {

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = trolleyIcon;
  };

  return (
    <div className="small-product-tile" style={{ marginBottom: '0.25rem' }}>
      <div className="row-1">
        <img src={item.image_url || trolleyIcon} onError={handleImageError} alt={item.name} className="product-image" />
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
            <span>${item.price.toFixed(2)}</span>
        </div>
        <div>
            <span>Qty: {item.quantity}</span>
        </div>
      </div>
    </div>
  );
};

export default DisplayOnlyProductTile;
