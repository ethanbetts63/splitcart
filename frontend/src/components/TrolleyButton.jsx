import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import splitCartSymbol from '../assets/trolley_v3.png';
import '../css/TrolleyButton.css';

const TrolleyButton = ({ onClick }) => {
  const { items } = useShoppingList();

  return (
    <button
      onClick={onClick}
      className="trolley-button"
    >
      <img src={splitCartSymbol} alt="Menu" style={{ width: '50px', height: '50px' }} />
      {items.length > 0 && (
        <span className="item-count">
          {items.length}
        </span>
      )}
    </button>
  );
};

export default TrolleyButton;
