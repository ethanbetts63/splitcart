import { useSearchParams } from 'react-router-dom';
import GridSourcer from '../components/GridSourcer';

const SearchResultsPage = () => {
  const [searchParams] = useSearchParams();
  const searchTerm = searchParams.get('q');
  const primaryCategorySlug = searchParams.get('primary_category_slug');
  const primaryCategorySlugs = searchParams.get('primary_category_slugs');

  // The logic for 'sourceUrl' can be added here later if needed.
  const sourceUrl = null;

  return (
    <div className="container mx-auto p-4">
      <GridSourcer 
        searchTerm={searchTerm}
        sourceUrl={sourceUrl}
        primaryCategorySlug={primaryCategorySlug}
        primaryCategorySlugs={primaryCategorySlugs}
      />
    </div>
  );
};

export default SearchResultsPage;