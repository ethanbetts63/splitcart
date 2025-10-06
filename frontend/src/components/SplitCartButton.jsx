import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useShoppingList } from '../context/ShoppingListContext';

const SplitCartButton = () => {
  const navigate = useNavigate();
  const { items, substitutes, selections, nearbyStoreIds } = useShoppingList();

  const handleClick = () => {
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

  return (
    <button style={{ backgroundColor: 'var(--primary)', color: 'white', padding: '0.75rem 1.5rem', fontSize: '1.25rem' }} onClick={handleClick}>
      Split My Cart!
    </button>
  );
};

export default SplitCartButton;