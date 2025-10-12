import { useShoppingList } from '../context/ShoppingListContext';
import '../css/AddToCartButton.css';

const AddToCartButton = ({ product, nearbyStoreIds, size }) => {
  const { items, addItem, updateItemQuantity, removeItem } = useShoppingList();
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = () => {
    addItem(product, 1, nearbyStoreIds);
  };

  const handleQuantityChange = (newQuantity) => {
    if (newQuantity > 0) {
      updateItemQuantity(product.id, newQuantity);
    } else {
      removeItem(product.id);
    }
  };

  const handleInputChange = (e) => {
    const newQuantity = parseInt(e.target.value, 10);
    if (!isNaN(newQuantity) && newQuantity > 0) {
        handleQuantityChange(newQuantity);
    }
  };

  const sizeClass = size ? ` ${size}` : '';

  if (existingItem) {
    return (
      <div className={`cart-trolley-controls${sizeClass}`}>
        <button onClick={() => handleQuantityChange(existingItem.quantity - 1)} className="quantity-btn decrement-btn">-</button>
        <input
          type="number"
          className="quantity-input"
          value={existingItem.quantity}
          onChange={handleInputChange}
          min="1"
        />
        <button onClick={() => handleQuantityChange(existingItem.quantity + 1)} className="quantity-btn increment-btn">+</button>
      </div>
    );
  }

  return (
    <button onClick={handleAdd} className={`add-to-cart-btn${sizeClass}`}>
      Add to Cart
    </button>
  );
};

export default AddToCartButton;