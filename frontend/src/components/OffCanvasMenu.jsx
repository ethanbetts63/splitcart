import React from 'react';
import '../css/OffCanvasMenu.css';
import ShoppingListComponent from './ShoppingListComponent';
import StoreMap from './StoreMap';
import LogoButton from './LogoButton';

const OffCanvasMenu = ({ isOpen, onClose, content, onLocationChange, onStoreSelectionChange, onNavigateHome }) => {
  let title = '';
  let body = null;

  if (content === 'trolley') {
    title = 'Shopping List';
    body = <ShoppingListComponent />;
  } else if (content === 'map') {
    title = 'Select Stores';
    body = (
      <>
        <p style={{ color: 'var(--text-muted)', marginTop: '0' }}>
          Double-click on the map to set your location.
          Check and uncheck specific stores below the map.
          The more stores you select, the more saving potential you allow.
        </p>
        <StoreMap onSelectionChange={onStoreSelectionChange} />
      </>
    );
  }

  return (
    <div className={`off-canvas-menu-right ${isOpen ? 'visible' : ''}`}>
      <div className="off-canvas-header">
        <LogoButton onClick={onNavigateHome} fontSize="60px" />
        <button onClick={onClose} className="close-button">&times;</button>
      </div>
      <div className="off-canvas-body">
        {body}
      </div>
      <div className="off-canvas-footer">
        <a onClick={onLocationChange} style={{ cursor: 'pointer' }}>Change Location</a>
      </div>
    </div>
  );
};

export default OffCanvasMenu;
