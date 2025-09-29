import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import ShoppingListComponent from './ShoppingListComponent';

const Header = ({ onShowLocationModal }) => {
  return (
    <Navbar bg="dark" variant="dark" expand="lg">
      <Container>
        <Navbar.Brand href="/">SplitCart</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
          </Nav>
          <Nav>
            <Nav.Link onClick={onShowLocationModal}>Change Location</Nav.Link>
          </Nav>
          <ShoppingListComponent />
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;