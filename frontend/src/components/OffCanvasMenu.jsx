import React, { useEffect } from 'react';
import '../css/OffCanvasMenu.css';
import ShoppingListComponent from './ShoppingListComponent';
import StoreMap from './StoreMap';
import cashTrolley from '../assets/cash_trolley.png';
import mapIcon from '../assets/edit_location.svg';
import NextButton from './NextButton';
import { useShoppingList } from '../context/ShoppingListContext';

const OffCanvasMenu = ({ isOpen, onClose, content, onLocationChange, onStoreSelectionChange, onNavigateHome }) => {
  const { items } = useShoppingList();

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
          <img src={mapIcon} alt="background" style={{
            display: 'block',
            marginLeft: 'auto',
            marginRight: 'auto',
            marginBottom: '0.5rem',
            marginTop: '-0rem',
            width: '50px',
            height: 'auto',
            objectFit: 'contain',
            opacity: 1,
          }} />
        )}
        {body}
      </div>

    </div>
  );
};

export default OffCanvasMenu;
