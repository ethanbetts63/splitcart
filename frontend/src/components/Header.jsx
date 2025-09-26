import React from 'react';
import { Navbar, Nav, Container } from 'react-bootstrap';
import ShoppingListComponent from './ShoppingListComponent';

const Header = () => {
  return (
    <Navbar bg="dark" variant="dark" expand="lg">
      <Container>
        <Navbar.Brand href="#home">SplitCart</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link href="#home">Home</Nav.Link>
            <Nav.Link href="#link">Link</Nav.Link>
          </Nav>
          <ShoppingListComponent />
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Header;
