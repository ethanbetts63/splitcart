import '../css/QuantityAdjuster.css';

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
      <button onClick={handleDecrement} className="quantity-adjuster-btn">-</button>
      <span className="quantity-adjuster-number">{quantity}</span>
      <button onClick={handleIncrement} className="quantity-adjuster-btn">+</button>
    </div>
  );
};

export default QuantityAdjuster;
