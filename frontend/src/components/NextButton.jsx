import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '../context/ShoppingListContext';
import '../css/NextButton.css';

const NextButton = ({ onClick, text = 'Next!' }) => {
  const navigate = useNavigate();
  const { items, substitutes, nearbyStoreIds } = useShoppingList();

  const internalHandleClick = () => {
    const itemsWithSubstitutes = items.filter(item => {
      const productSubs = substitutes[item.product.id];
      return productSubs && productSubs.length > 0;
    });

    if (itemsWithSubstitutes.length === 0) {
      // No items have substitutes, go straight to final cart
      const formattedCart = items.map(item => [
        { product_id: item.product.id, quantity: item.quantity || 1 }
      ]);
      navigate('/final-cart', { state: { cart: formattedCart, store_ids: nearbyStoreIds } });
    } else {
      // Some items have substitutes, go to substitution page with only those items
      navigate('/split-cart', { state: { itemsToReview: itemsWithSubstitutes } });
    }
  };

  const finalOnClick = onClick || internalHandleClick;

  return (
    <button 
      className="dashing-fill"
      onClick={finalOnClick}
    >
      <span className="dashing-fill-text">{text}</span>
    </button>
  );
};

export default NextButton;
