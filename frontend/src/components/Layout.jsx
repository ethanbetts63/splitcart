import React from 'react';
import { Outlet } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import SearchHeader from './SearchHeader';

const Layout = ({ searchTerm, setSearchTerm, children }) => {
  return (
    <>
      <SearchHeader searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <Container fluid>
        {children}
      </Container>
    </>
  );
};

export default Layout;
