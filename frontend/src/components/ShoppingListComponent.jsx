import React from 'react';
import { useShoppingList } from '../context/ShoppingListContext';
import trolleyIcon from '../assets/trolley_v3.png';
import QuantityAdjuster from './QuantityAdjuster';

import { Button } from 'react-bootstrap';

const ShoppingListComponent = () => {
  const { items, selections, updateItemQuantity, removeItem } = useShoppingList();

  const handleImageError = (e) => {
    e.target.onerror = null; // Prevent infinite loop if placeholder also fails
    e.target.src = trolleyIcon;
  };

  return (
    <>
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
          <div style={{ backgroundColor: 'var(--colorp3)', padding: '0.5rem', borderRadius: '8px' }}>Your list is empty</div>
        ) : (
          items.map(item => {
            const itemSelections = selections[item.product.id] || [];
            const substitutes = itemSelections.filter(p => p.id !== item.product.id);

            return (
              <div key={item.product.id} style={{ backgroundColor: 'var(--colorbody)', padding: '0.5rem', marginBottom: '0.5rem', borderRadius: '8px', display: 'flex', flexDirection: 'column' }}>
                {/* First Row */}
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <img src={item.product.image_url || trolleyIcon} onError={handleImageError} alt={item.product.name} style={{ width: '50px', height: '50px', marginRight: '1rem', borderRadius: '4px' }} />
                  <div style={{ flexGrow: 1 }}>
                    <strong>{item.product.name}</strong>
                    <div>
                      <small className="text-muted">{item.product.brand}</small>
                      <span style={{ backgroundColor: 'var(--colorp2)', color: 'white', padding: '0.2rem 0.4rem', borderRadius: '8px', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                        {item.product.size}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Second Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.5rem' }}>
                  <div>
                    <small className="text-muted">Price: $X.XX - $Y.YY</small>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <QuantityAdjuster 
                      quantity={item.quantity} 
                      onQuantityChange={(newQuantity) => updateItemQuantity(item.product.id, newQuantity)} 
                    />
                    <Button variant="danger" size="sm" onClick={() => removeItem(item.product.id)} style={{ padding: '0.1rem 0.5rem', fontSize: '1rem' }}>Remove</Button>
                  </div>
                </div>

                {substitutes.length > 0 && (
                  <div style={{ paddingLeft: '1rem', marginTop: '0.5rem' }}>
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