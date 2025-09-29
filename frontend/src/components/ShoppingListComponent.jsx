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
          items.map(item => (
            <ListGroup.Item key={item.product.id}>
              {item.product.name} (x{item.quantity})
            </ListGroup.Item>
          ))
        )}
      </ListGroup>
    </>
  );
};

export default ShoppingListComponent;