"use client";

import { useSearchParams } from 'next/navigation';
import GridSourcer from '../components/GridSourcer';
import Seo from '../components/Seo';

const SearchResultsPage = () => {
  const searchParams = useSearchParams();
  const searchTerm = searchParams?.get('q') ?? null;
  const primaryCategorySlug = searchParams?.get('primary_category_slug') ?? null;
  const bargainCompany = searchParams?.get('bargain_company') ?? null;

  // The logic for 'sourceUrl' can be added here later if needed.
  const sourceUrl = null;

  return (
    <div className="container mx-auto p-4">
      <Seo title="Search - SplitCart" noindex />
      <GridSourcer
        searchTerm={searchTerm}
        sourceUrl={sourceUrl}
        primaryCategorySlug={primaryCategorySlug}
        bargainCompany={bargainCompany}
      />
    </div>
  );
};

export default SearchResultsPage;
