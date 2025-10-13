import React from 'react';
import { useLocation } from 'react-router-dom';
import GridSourcer from '../components/GridSourcer';

const ProductListPage = ({ nearbyStoreIds }) => {
  console.log('ProductListPage.jsx rendered');
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);

  const searchTerm = queryParams.get('search');
  const source = queryParams.get('source'); // e.g., 'bargains'

  let sourceUrl = null;
  if (source === 'bargains') {
    sourceUrl = '/api/products/bargains/';
  } else if (source === 'all') {
    sourceUrl = '/api/products/';
  }

  // If neither searchTerm nor sourceUrl is provided, default to all products
  if (!searchTerm && !sourceUrl) {
    sourceUrl = '/api/products/';
  }

  return (
    <div style={{ marginTop: '2rem' }}>
      <GridSourcer 
        searchTerm={searchTerm}
        sourceUrl={sourceUrl}
        nearbyStoreIds={nearbyStoreIds}
      />
    </div>
  );
};

export default ProductListPage;
