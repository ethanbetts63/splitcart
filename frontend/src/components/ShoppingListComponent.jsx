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
            <ListGroup.Item key={slot[0].product.id} className="d-flex justify-content-between align-items-center">
              {slot[0].product.name} (x{slot[0].quantity})
              {slot.length > 1 && (
                <Badge bg="info" pill>
                  {slot.length - 1} substitutes
                </Badge>
              )}
            </ListGroup.Item>
          ))
        )}
      </ListGroup>
    </>
  );
};

export default ShoppingListComponent;