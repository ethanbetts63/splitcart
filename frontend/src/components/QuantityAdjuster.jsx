import React from 'react';

const QuantityAdjuster = ({ quantity, onQuantityChange }) => {
  const handleDecrement = () => {
    if (quantity > 0) {
      onQuantityChange(quantity - 1);
    }
  };

  const handleIncrement = () => {
    onQuantityChange(quantity + 1);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <button onClick={handleDecrement} style={{ background: 'var(--colorp2)', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '4px', padding: '0.1rem 0.5rem' }}>-</button>
      <span style={{ padding: '0 0.5rem', fontSize: '1.2rem' }}>{quantity}</span>
      <button onClick={handleIncrement} style={{ background: 'var(--colorp2)', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '4px', padding: '0.1rem 0.5rem' }}>+</button>
    </div>
  );
};

export default QuantityAdjuster;
