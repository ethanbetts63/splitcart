import React from 'react';
import '../css/OffCanvasMenu.css';
import ShoppingListComponent from './ShoppingListComponent';
import StoreMap from './StoreMap';
import cashTrolley from '../assets/cash_trolley.png'; // Import the image
import mapIcon from '../assets/edit_location.svg';

const OffCanvasMenu = ({ isOpen, onClose, content, onLocationChange, onStoreSelectionChange, onNavigateHome }) => {
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
      <div className="off-canvas-header">
      </div>
      <div className="off-canvas-body">
        {content === 'map' && (
          <img src={mapIcon} alt="background" style={{
            display: 'block',
            marginLeft: 'auto',
            marginRight: 'auto',
            marginBottom: '0.5rem',
            marginTop: '-1rem',
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
