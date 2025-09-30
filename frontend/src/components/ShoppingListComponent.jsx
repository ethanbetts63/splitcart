import React from 'react';
import { ListGroup, Badge } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const ShoppingListComponent = () => {
  const { items } = useShoppingList();

  return (
    <>
      <h5>Shopping List <Badge bg="secondary">{items.length}</Badge></h5>
      <ListGroup>
        {items.length === 0 ? (
          <ListGroup.Item>Your list is empty</ListGroup.Item>
        ) : (
          items.map(slot => (
            <ListGroup.Item key={slot[0].product.id}>
              <div>
                <strong>{slot[0].product.name} (x{slot[0].quantity})</strong>
              </div>
              {slot.length > 1 && (
                <div className="ps-2">
                  <small className="text-muted">Substitutes:</small>
                  {slot.slice(1).map(subItem => (
                    <div key={subItem.product.id} className="ps-3">
                      <small>{subItem.product.name}</small>
                    </div>
                  ))}
                </div>
              )}
            </ListGroup.Item>
          ))
        )}
      </ListGroup>
    </>
  );
};

export default ShoppingListComponent;