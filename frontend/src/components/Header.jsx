import React, { useState } from 'react';
import { Button, Offcanvas, Nav } from 'react-bootstrap';
import ShoppingListComponent from './ShoppingListComponent';
import splitCartSymbol from '../assets/SplitCart_symbol.png';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { items } = useShoppingList();

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
        <img src={splitCartSymbol} alt="Menu" style={{ width: '60px', height: '60px' }} />
      </Button>

      {items.length > 0 && (
        <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1050, padding: '1rem' }}>
          <Button style={{ backgroundColor: '#FB641F', color: 'white', marginRight: '1rem' }}>Trolley</Button>
          <Button style={{ backgroundColor: '#1CC3B9', color: 'white' }}>Split My Cart!</Button>
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