import React, { useState } from 'react';
import { Button, Offcanvas, Nav } from 'react-bootstrap';
import ShoppingListComponent from './ShoppingListComponent';
import splitCartSymbol from '../assets/SplitCart_symbol.png';

const Header = ({ onShowLocationModal }) => {
  const [showMenu, setShowMenu] = useState(false);

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
        <img src={splitCartSymbol} alt="Menu" style={{ width: '40px', height: '40px' }} />
      </Button>

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
