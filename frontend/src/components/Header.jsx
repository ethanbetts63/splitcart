import React, { useState } from 'react';
import { Button, Offcanvas, Nav, Badge } from 'react-bootstrap';
import { useLocation, useNavigate } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import SplitCartButton from './SplitCartButton';
import splitCartSymbol from '../assets/trolley_v3.webp';
import splitCartTitle from '../assets/splitcart_v5.png';
import mapIcon from '../assets/edit_location_large.svg';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal, onShowStoreMap, setSearchTerm }) => {
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
        style={{ position: 'absolute', top: -50, left: -30, zIndex: 1030 }}
      >
        <img src={splitCartSymbol} alt="Menu" style={{ width: '180px', height: '180px' }} />
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

      <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1030, padding: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <Button variant="link" onClick={onShowStoreMap} className="p-0 me-2">
          <img src={mapIcon} alt="Map" style={{ width: '90px', height: '70px' }} />
        </Button>
        {items.length > 0 && location.pathname !== '/split-cart' && location.pathname !== '/final-cart' && <SplitCartButton />}
      </div>

      <Offcanvas show={showMenu} onHide={handleClose} placement="start">
        <Offcanvas.Header closeButton>
          <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
            <img src={splitCartTitle} alt="SplitCart" style={{ maxWidth: '250px' }} />
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