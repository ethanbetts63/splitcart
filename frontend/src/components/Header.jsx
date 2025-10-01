import React, { useState } from 'react';
import { Button, Offcanvas, Nav, Badge } from 'react-bootstrap';
import { useLocation, useNavigate } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import SplitCartButton from './SplitCartButton';
import splitCartSymbol from '../assets/SplitCart_symbol_v2.png';
import splitCartTitle from '../assets/splitcart_title_v2.png';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal, setSearchTerm }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { items } = useShoppingList();
  const location = useLocation();
  const navigate = useNavigate();

  const handleClose = () => setShowMenu(false);
  const handleShow = () => setShowMenu(true);

  const handleHomeClick = () => {
    handleClose();
    if (setSearchTerm) {
      setSearchTerm('');
    }
    navigate('/');
  };

  return (
    <>
      <Button
        variant="link"
        onClick={handleShow}
        className="p-0 m-3"
        style={{ position: 'absolute', top: 0, left: 0, zIndex: 1030 }}
      >
        <img src={splitCartSymbol} alt="Menu" style={{ width: '120px', height: '100px' }} />
        {items.length > 0 && (
          <Badge
            bg="danger"
            pill
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              fontSize: '0.8em',
            }}
          >
            {items.length}
          </Badge>
        )}
      </Button>

      {items.length > 0 && (
        <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1050, padding: '1.5rem', display: 'flex', alignItems: 'center' }}>
          {location.pathname !== '/split-cart' && location.pathname !== '/final-cart' && <SplitCartButton />}
        </div>
      )}

      <Offcanvas show={showMenu} onHide={handleClose} placement="start">
        <Offcanvas.Header closeButton>
          <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
            <img src={splitCartTitle} alt="SplitCart" style={{ maxWidth: '200px' }} />
          </div>
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