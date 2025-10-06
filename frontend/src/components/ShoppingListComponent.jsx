import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';

const ShoppingListComponent = () => {
  const { items, selections } = useShoppingList();

  return (
    <>
      <h5>Shopping List <span style={{ backgroundColor: 'var(--secondary)', color: 'white', borderRadius: '12px', padding: '0.2em 0.6em' }}>{items.length}</span></h5>
      <div>
        {items.length === 0 ? (
          <div style={{ border: '1px solid var(--border)', padding: '1rem' }}>Your list is empty</div>
        ) : (
          items.map(item => {
            const itemSelections = selections[item.product.id] || [];
            const substitutes = itemSelections.filter(p => p.id !== item.product.id);

            return (
              <div key={item.product.id} style={{ border: '1px solid var(--border)', padding: '1rem', marginBottom: '0.5rem' }}>
                <div>
                  <strong>{item.product.name} (x{item.quantity})</strong>
                </div>
                {substitutes.length > 0 && (
                  <div style={{ paddingLeft: '1rem' }}>
                    <small style={{ color: 'var(--text-muted)' }}>Substitutes:</small>
                    {substitutes.map(sub => (
                      <div key={sub.id} style={{ paddingLeft: '1.5rem' }}>
                        <small>{sub.name}</small>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </>
  );
};

export default ShoppingListComponent;