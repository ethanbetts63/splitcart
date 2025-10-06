import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import TrolleyButton from './TrolleyButton';
import mapIcon from '../assets/edit_location_large.svg';

const Header = ({ onShowLocationModal, onShowStoreMap, setSearchTerm }) => {
  const [showMenu, setShowMenu] = useState(false);
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
      <TrolleyButton onClick={handleShow} />

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