import React from 'react';
import { Dropdown, Badge } from 'react-bootstrap';
import { useShoppingList } from '../context/ShoppingListContext';

const ShoppingListComponent = () => {
  const { items } = useShoppingList();

  return (
    <Dropdown>
      <Dropdown.Toggle variant="success" id="dropdown-basic">
        Shopping List <Badge bg="secondary">{items.length}</Badge>
      </Dropdown.Toggle>

      <Dropdown.Menu>
        {items.length === 0 ? (
          <Dropdown.Item>Your list is empty</Dropdown.Item>
        ) : (
          items.map(item => (
            <Dropdown.Item key={item.product.id}>
              {item.product.name} (x{item.quantity})
            </Dropdown.Item>
          ))
        )}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default ShoppingListComponent;
