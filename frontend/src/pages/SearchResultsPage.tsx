import { useSearchParams } from 'react-router-dom';
import GridSourcer from '../components/GridSourcer';

const SearchResultsPage = () => {
  const [searchParams] = useSearchParams();
  const searchTerm = searchParams.get('q');
  const categorySlug = searchParams.get('category_slug');
  const superCategory = searchParams.get('super_category');

  // The logic for 'sourceUrl' can be added here later if needed.
  const sourceUrl = null;

  return (
    <div className="container mx-auto p-4">
      <GridSourcer 
        searchTerm={searchTerm}
        sourceUrl={sourceUrl}
        categorySlug={categorySlug}
        superCategory={superCategory}
      />
    </div>
  );
};

export default SearchResultsPage;