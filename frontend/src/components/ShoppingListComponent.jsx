import React from 'react';
import { ListGroup, Badge } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const ShoppingListComponent = () => {
  const { items, selections } = useShoppingList();

  return (
    <>
      <h5>Shopping List <Badge bg="secondary">{items.length}</Badge></h5>
      <ListGroup>
        {items.length === 0 ? (
          <ListGroup.Item>Your list is empty</ListGroup.Item>
        ) : (
          items.map(item => {
            const itemSelections = selections[item.product.id] || [];
            const substitutes = itemSelections.filter(p => p.id !== item.product.id);

            return (
              <ListGroup.Item key={item.product.id}>
                <div>
                  <strong>{item.product.name} (x{item.quantity})</strong>
                </div>
                {substitutes.length > 0 && (
                  <div className="ps-2">
                    <small className="text-muted">Substitutes:</small>
                    {substitutes.map(sub => (
                      <div key={sub.id} className="ps-3">
                        <small>{sub.name}</small>
                      </div>
                    ))}
                  </div>
                )}
              </ListGroup.Item>
            );
          })
        )}
      </ListGroup>
    </>
  );
};

export default ShoppingListComponent;