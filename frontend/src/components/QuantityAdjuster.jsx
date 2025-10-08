const QuantityAdjuster = ({ quantity, onQuantityChange, className }) => {
  const handleDecrement = () => {
    if (quantity > 0) {
      onQuantityChange(quantity - 1);
    }
  };

  const handleIncrement = () => {
    onQuantityChange(quantity + 1);
  };

  return (
    <div className={className} style={{ display: 'flex', alignItems: 'baseline' }}>
      <button onClick={handleDecrement} style={{ background: 'var(--colorp2)', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '4px', padding: '0.4rem 0.8rem' }}>-</button>
      <span style={{ padding: '0 0.5rem', fontSize: '2rem'}}>{quantity}</span>
      <button onClick={handleIncrement} style={{ background: 'var(--colorp2)', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '4px', padding: '0.4rem 0.8rem' }}>+</button>
    </div>
  );
};

export default QuantityAdjuster;
