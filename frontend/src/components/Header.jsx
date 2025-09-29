import React, { useState } from 'react';
import { Button, Offcanvas, Nav, Dropdown, Badge } from 'react-bootstrap';
import { useLocation } from 'react-router-dom';
import ShoppingListComponent from './ShoppingListComponent';
import SplitCartButton from './SplitCartButton';
import splitCartSymbol from '../assets/SplitCart_symbol_v2.png';
import { useShoppingList } from '../context/ShoppingListContext';

const Header = ({ onShowLocationModal }) => {
  const [showMenu, setShowMenu] = useState(false);
  const { items, substitutionChoices } = useShoppingList();
  const location = useLocation();

  const handleClose = () => setShowMenu(false);
  const handleShow = () => setShowMenu(true);

  return (
    <>
      <Button
        variant="link"
        onClick={handleShow}
        className="p-0 m-3"
        style={{ position: 'absolute', top: 0, left: 0, zIndex: 1050 }}
      >
        <img src={splitCartSymbol} alt="Menu" style={{ width: '80px', height: '80px' }} />
      </Button>

      {items.length > 0 && (
        <div style={{ position: 'absolute', top: 0, right: 0, zIndex: 1050, padding: '1.5rem', display: 'flex', alignItems: 'center' }}>
          <Dropdown>
            <Dropdown.Toggle style={{ backgroundColor: '#FB641F', color: 'white', marginRight: '1rem' }} size="lg">
              Trolley <Badge bg="light" text="dark">{items.length}</Badge>
            </Dropdown.Toggle>
            <Dropdown.Menu>
              {items.map(item => {
                const choice = substitutionChoices.find(c => c.originalProductId === item.product.id);
                const selectedProductIds = choice ? choice.selectedIds : [item.product.id];
                
                // Find the actual product objects for the selected IDs
                const selectedProducts = selectedProductIds.map(id => 
                  items.find(i => i.product.id === id)?.product || 
                  // Fallback: if not in items (e.g., a substitute not yet added to main list),
                  // we might need to fetch it or rely on a more comprehensive product list.
                  // For now, we'll just use a placeholder or the original product if not found.
                  (id === item.product.id ? item.product : { name: `Product ID: ${id}` }) 
                );

                return (
                  <Dropdown.Item key={item.product.id}>
                    {selectedProducts.map((p, index) => (
                      <div key={p.id || index}>{p.name} (x{item.quantity})</div>
                    ))}
                  </Dropdown.Item>
                );
              })}
            </Dropdown.Menu>
          </Dropdown>
          {location.pathname !== '/split-cart' && <SplitCartButton />}
        </div>
      )}

      <Offcanvas show={showMenu} onHide={handleClose} placement="start">
        <Offcanvas.Header closeButton>
          <Offcanvas.Title>Menu</Offcanvas.Title>
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