import React from 'react';
import '../css/OffCanvasMenu.css';
import ShoppingListComponent from './ShoppingListComponent';
import StoreMap from './StoreMap';
import cashTrolley from '../assets/cash_trolley.png'; // Import the image

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
      <img src={cashTrolley} alt="background" style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        zIndex: -1,
        opacity: 0.1,
        maskImage: 'radial-gradient(ellipse at center, black 50%, transparent 95%)'
      }} />
      <div className="off-canvas-header">
      </div>
      <div className="off-canvas-body">
        {body}
      </div>

    </div>
  );
};

export default OffCanvasMenu;
