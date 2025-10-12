import React, { useState, useEffect } from 'react';
import '../css/OffCanvasMenu.css';
import ShoppingListComponent from './ShoppingListComponent';
import StoreMap from './StoreMap';
import cashTrolley from '../assets/cash_trolley.png';
import mapIcon from '../assets/edit_location.svg';
import NextButton from './NextButton';
import { useShoppingList } from '../context/ShoppingListContext';

const OffCanvasMenu = ({ isOpen, onClose, content, onLocationChange, onStoreSelectionChange, onNavigateHome }) => {
  const { items } = useShoppingList();
  const [postcode, setPostcode] = useState('');
  const [radius, setRadius] = useState(10);
  const [error, setError] = useState(null);

  const handlePostcodeSearch = async () => {
    if (!postcode) {
      setError("Please enter a postcode.");
      return;
    }
    if (!/^\d{4}$/.test(postcode)) {
      setError("Please enter a valid 4-digit postcode.");
      return;
    }
    setError(null);
    try {
      const response = await fetch(`/api/postcodes/search/?postcode=${postcode}`);
      if (response.ok) {
        const data = await response.json();
        onLocationChange({ latitude: data.latitude, longitude: data.longitude, radius });
        onClose();
      } else {
        setError("Postcode not found.");
      }
    } catch (err) {
      setError("An error occurred while searching for the postcode.");
    }
  };

  useEffect(() => {
    if (isOpen) {
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    } else {
      document.body.style.overflow = 'unset';
      document.body.style.paddingRight = '0';
    }

    return () => {
      document.body.style.overflow = 'unset';
      document.body.style.paddingRight = '0';
    };
  }, [isOpen]);

  let title = '';
  let body = null;

  if (content === 'trolley') {
    title = 'Shopping List';
    body = <ShoppingListComponent />;
  } else if (content === 'map') {
    title = 'Select Stores';
    body = <StoreMap onSelectionChange={onStoreSelectionChange} />;
  }

  return (
    <div className={`off-canvas-menu-right ${isOpen ? 'visible' : ''}`}>
      <div className="off-canvas-header" style={{ position: 'relative' }}>
        <h2 style={{ margin: 0 }}>{title}</h2>
        {content === 'trolley' && (
          <div style={{ position: 'absolute', top: '50%', right: '1rem', transform: 'translateY(-50%)' }}>
            <NextButton />
          </div>
        )}
      </div>

      {content === 'trolley' && (
        <img src={cashTrolley} alt="background" style={{
          position: 'absolute',
          top: '50%',
          marginTop: '85px',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '80%',
          height: 'auto',
          objectFit: 'contain',
          zIndex: -1,
          opacity: 1,
          maskImage: 'radial-gradient(ellipse at center, black 50%, transparent 70%)'
        }} />
      )}

      <div className="off-canvas-body">
        {content === 'map' && (
          <div style={{ padding: '1rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <label>Postcode</label>
              <div style={{ display: 'flex' }}>
                <input
                  type="text"
                  placeholder="4-digit postcode"
                  value={postcode}
                  onChange={(e) => setPostcode(e.target.value)}
                  maxLength="4"
                  style={{ width: '100%', padding: '0.5rem' }}
                />
                <button type="button" onClick={handlePostcodeSearch} style={{ marginLeft: '0.5rem' }}>Search</button>
              </div>
              {error && <p style={{ color: 'red' }}>{error}</p>}
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label>Search Radius (km)</label>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <button type="button" onClick={() => setRadius(Math.max(1, radius - 1))}>-</button>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={radius}
                  onChange={(e) => setRadius(parseInt(e.target.value, 10))}
                  style={{ flexGrow: 1, margin: '0 0.5rem' }}
                />
                <span>{radius} km</span>
              </div>
            </div>
          </div>
        )}
        {body}
      </div>

    </div>
  );
};

export default OffCanvasMenu;
