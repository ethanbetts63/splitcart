import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import splitCartSymbol from '../assets/trolley_v3.png';
import mapIcon from '../assets/edit_location_large.svg';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal, onShowStoreMap, setSearchTerm }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { items } = useShoppingList();
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
      <button
        onClick={handleShow}
        style={{ position: 'absolute', top: 0, left: 0, zIndex: 1030, background: 'none', border: 'none', padding: 0, margin: '1.5rem' }}
      >
        <img src={splitCartSymbol} alt="Menu" style={{ width: '100px', height: '100px' }} />
        {items.length > 0 && (
          <span
            style={{
              position: 'absolute',
              top: '10px',
              right: '10px',
              fontSize: '0.8em',
              backgroundColor: 'red',
              color: 'white',
              borderRadius: '50%',
              padding: '0.2em 0.6em'
            }}
          >
            {items.length}
          </span>
        )}
      </button>

      <div style={{ position: 'absolute', top: 15, right: 0, zIndex: 1030, padding: '1.5rem', display: 'flex', alignItems: 'center' }}>
        <button onClick={onShowStoreMap} style={{ background: 'none', border: 'none', padding: 0, marginRight: '0.5rem' }}>
          <img src={mapIcon} alt="Map" style={{ width: '90px', height: '70px' }} />
        </button>
      </div>

            <div className={`off-canvas-menu-left ${showMenu ? 'visible' : ''}`}>
        <div style={{ padding: '1rem' }}>
          <button onClick={handleClose} style={{ float: 'right', background: 'none', border: 'none', fontSize: '1.5rem' }}>&times;</button>
          <div onClick={handleHomeClick} style={{ cursor: 'pointer' }}>
                        <h1 style={{ fontFamily: 'Vollkorn', fontStyle: 'italic', fontSize: '60px', color: 'var(--primary)', textAlign: 'center' }}>
              splitcart
            </h1>
          </div>
        </div>
        <div style={{ padding: '1rem' }}>
          <nav style={{ display: 'flex', flexDirection: 'column' }}>
            <a onClick={() => { onShowLocationModal(); handleClose(); }} style={{ cursor: 'pointer' }}>Change Location</a>
            <hr />
            <ShoppingListComponent />
          </nav>
        </div>
      </div>
    </>
  );
};

export default Header;