import React from 'react';
import { useSearchParams } from 'react-router-dom';
import GridSourcer from '../components/GridSourcer';

const SearchResultsPage = () => {
  const [searchParams] = useSearchParams();
  const searchTerm = searchParams.get('q');
  const categorySlug = searchParams.get('category_slug');

  // The logic for 'sourceUrl' can be added here later if needed.
  const sourceUrl = null;

  return (
    <div className="container mx-auto p-4">
      <GridSourcer 
        searchTerm={searchTerm}
        sourceUrl={sourceUrl}
        categorySlug={categorySlug}
      />
    </div>
  );
};

export default SearchResultsPage;