import React from 'react';
import { Outlet } from 'react-router-dom';
import SearchHeader from './SearchHeader';

const Layout = ({ searchTerm, setSearchTerm, children }) => {
  return (
    <>
      <SearchHeader searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <div>
        {children}
      </div>
    </>
  );
};

export default Layout;
