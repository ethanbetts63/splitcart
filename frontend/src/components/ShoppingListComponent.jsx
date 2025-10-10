import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import trolleyIcon from '../assets/shopping_cart.svg';
import SmallProductTile from './SmallProductTile';

const ShoppingListComponent = () => {
  const { items, updateItemQuantity, removeItem } = useShoppingList();

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img src={trolleyIcon} alt="Trolley" style={{ width: '80px', height: '80px' }} />
          {items.length > 0 && (
            <span style={{
              position: 'absolute',
              top: '-5px',
              right: '-5px',
              fontSize: '0.8em',
              backgroundColor: 'var(--danger)',
              color: 'white',
              borderRadius: '50%',
              padding: '0.2em 0.6em'
            }}>
              {items.length}
            </span>
          )}
        </div>
      </div>
      <div>
        {items.length === 0 ? (
          <div style={{ backgroundColor: 'var(--colorp3)', padding: '0.5rem', borderRadius: '8px', fontSize: '1.3rem' }}>Your list is empty.</div>
        ) : (
          items.map(item => (
            <SmallProductTile 
              key={item.product.id}
              item={item}
              onRemove={removeItem}
              onQuantityChange={updateItemQuantity}
              showSubstitutes={true}
            />
          ))
        )}
      </div>
    </>
  );
};

export default ShoppingListComponent;