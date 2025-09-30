import React, { useState } from 'react';
import { Button, Offcanvas, Nav, Dropdown, Badge } from 'react-bootstrap';
import { useLocation } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import SplitCartButton from './SplitCartButton';
import splitCartSymbol from '../assets/SplitCart_symbol_v2.png';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { items } = useShoppingList(); // Removed substitutionChoices
  const location = useLocation();

  const handleClose = () => setShowMenu(false);
  const handleShow = () => setShowMenu(true);

  return (
    <>
      <Button
        variant="link"
        onClick={handleShow}
        className="p-0 m-3"
        style={{ position: 'absolute', top: 0, left: 0, zIndex: 1050 }}
      >
        <img src={splitCartSymbol} alt="Menu" style={{ width: '80px', height: '80px' }} />
      </Button>

      {items.length > 0 && (
        <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1050, padding: '1.5rem', display: 'flex', alignItems: 'center' }}>
          <Dropdown>
            <Dropdown.Toggle style={{ backgroundColor: '#FB641F', color: 'white', marginRight: '1rem' }} size="lg">
              Trolley <Badge bg="light" text="dark">{items.length}</Badge>
            </Dropdown.Toggle>
            <Dropdown.Menu>
              {items.map(slot => {
                const primaryItem = slot[0];
                return (
                  <Dropdown.Item key={primaryItem.product.id}>
                    <strong>{primaryItem.product.name} (x{primaryItem.quantity})</strong>
                    {slot.length > 1 && (
                      <div className="ps-2">
                        <small className="text-muted">Subs:</small>
                        {slot.slice(1).map(subItem => (
                          <div key={subItem.product.id} className="ps-3">
                            <small>{subItem.product.name}</small>
                          </div>
                        ))}
                      </div>
                    )}
                  </Dropdown.Item>
                );
              })}
            </Dropdown.Menu>
          </Dropdown>
          {location.pathname !== '/split-cart' && <SplitCartButton />}
        </div>
      )}

      <Offcanvas show={showMenu} onHide={handleClose} placement="start">
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Menu</Offcanvas.Title>
        </Offcanvas.Header>
        <Offcanvas.Body>
          <Nav className="flex-column">
            <Nav.Link onClick={() => { onShowLocationModal(); handleClose(); }}>Change Location</Nav.Link>
            <hr />
            <ShoppingListComponent />
          </Nav>
        </Offcanvas.Body>
      </Offcanvas>
    </>
  );
};

export default Header;