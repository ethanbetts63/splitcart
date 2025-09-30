import React from 'react';
import { Container } from 'react-bootstrap';

const Footer = () => {
  return (
    <footer className="footer mt-auto py-3 text-dark">
      <Container className="text-center">
        <span>&copy; {new Date().getFullYear()} SplitCart</span>
      </Container>
    </footer>
  );
};

export default Footer;