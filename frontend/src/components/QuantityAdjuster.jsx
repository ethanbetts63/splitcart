import React from 'react';
import '../css/QuantityAdjuster.css';

const QuantityAdjuster = ({ quantity, onQuantityChange }) => {
  const handleDecrement = () => {
    onQuantityChange(quantity - 1);
  };

  const handleIncrement = () => {
    onQuantityChange(quantity + 1);
  };

  return (
    <div className="quantity-adjuster">
      <button onClick={handleDecrement} className="quantity-btn">-</button>
      <span className="quantity-display">{quantity}</span>
      <button onClick={handleIncrement} className="quantity-btn">+</button>
    </div>
  );
};

export default QuantityAdjuster;
