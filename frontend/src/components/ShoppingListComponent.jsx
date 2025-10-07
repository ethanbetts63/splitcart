import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import trolleyIcon from '../assets/trolley_v3.png';

const ShoppingListComponent = () => {
  const { items, selections } = useShoppingList();

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = trolleyIcon;
  };

  return (
    <div style={{ backgroundColor: 'var(--bg-dark)', padding: '1rem', borderRadius: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img src={trolleyIcon} alt="Trolley" style={{ width: '60px', height: '60px' }} />
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
          <div style={{ backgroundColor: 'var(--bg-light)', padding: '1rem', borderRadius: '8px' }}>Your list is empty</div>
        ) : (
          items.map(item => {
            const itemSelections = selections[item.product.id] || [];
            const substitutes = itemSelections.filter(p => p.id !== item.product.id);

            return (
              <div key={item.product.id} style={{ display: 'flex', alignItems: 'center', backgroundColor: 'var(--bg-light)', padding: '1rem', marginBottom: '0.5rem', borderRadius: '8px' }}>
                <img src={item.product.image_url || trolleyIcon} onError={handleImageError} alt={item.product.name} style={{ width: '50px', height: '50px', marginRight: '1rem', borderRadius: '4px' }} />
                <div>
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
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ShoppingListComponent;