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
    body = <StoreMap onSelectionChange={onStoreSelectionChange} />;
  }

  return (
    <div className={`off-canvas-menu-right ${isOpen ? 'visible' : ''}`}>
      <div className="off-canvas-header">
      </div>
      <div className="off-canvas-body">
        {body}
      </div>

    </div>
  );
};

export default OffCanvasMenu;
