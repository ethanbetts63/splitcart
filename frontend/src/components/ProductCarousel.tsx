import React, { memo, useEffect, useRef } from 'react';
import SkeletonProductTile from "./SkeletonProductTile";
import ProductTile from "./ProductTile";
import { Link } from 'react-router-dom';
import type { Product } from '../types';
import JsonLdItemList from './JsonLdItemList';

interface ProductCarouselProps {
  sourceUrl: string;
  storeIds?: number[];
  title: string;
  searchQuery?: string;
  isDefaultStores?: boolean;
  primaryCategorySlug?: string;
  primaryCategorySlugs?: string[];
  pillarPageLinkSlug?: string;
  onValidation?: (slug: string, isValid: boolean, slot: number) => void;
  slot?: number; // Make slot optional
  dataKey?: string; // Key to access product data in a nested object
  minProducts?: number; // Minimum number of products to render the carousel
}

import { useApiQuery } from '@/hooks/useApiQuery';

const ProductCarouselComponent: React.FC<ProductCarouselProps> = ({ sourceUrl, storeIds, title, searchQuery, isDefaultStores, primaryCategorySlug, primaryCategorySlugs, pillarPageLinkSlug, onValidation, slot, dataKey, minProducts = 4 }) => {
  const [baseUrl, queryString] = sourceUrl.split('?');
  const params = new URLSearchParams(queryString || '');
  if (storeIds && storeIds.length > 0) {
    params.set('store_ids', storeIds.join(','));
  }
  if (primaryCategorySlugs && primaryCategorySlugs.length > 0) {
    params.set('primary_category_slugs', primaryCategorySlugs.join(','));
  } else if (primaryCategorySlug) {
    params.set('primary_category_slug', primaryCategorySlug);
  }
  // Add a limit to the query, but not for substitutes
  if (!sourceUrl.includes('substitutes')) {
    params.set('limit', '20');
    // Add the special ordering for carousels
    params.set('ordering', 'carousel_default');
  }


  const finalUrl = `${baseUrl}?${params.toString()}`;

  const { data: responseData, isLoading, error, isFetched } = useApiQuery<any>(
    ['products', title, finalUrl],
    finalUrl,
    {},
    { enabled: !!storeIds && storeIds.length > 0, refetchOnWindowFocus: false, staleTime: 1000 * 60 * 10 } // 10 minutes
  );

  // Ref to prevent calling onValidation multiple times
  const validationCalled = useRef(false);

  // Process the response to get the final list of products
  const products: Product[] = React.useMemo(() => {
    if (!responseData) return [];
    
    // Handle responses that are direct arrays (like substitutes) vs objects with a 'results' key
    const results = Array.isArray(responseData) ? responseData : responseData.results || [];

    // If a dataKey is provided, map over the results to extract the nested product data
    if (dataKey) {
      return results.map((item: any) => item[dataKey]).filter(Boolean); // filter out null/undefined
    }

    return results;
  }, [responseData, dataKey]);

  useEffect(() => {
    if (isFetched && onValidation && (primaryCategorySlug || primaryCategorySlugs) && !validationCalled.current && slot !== undefined) {
      const identifier = primaryCategorySlugs ? primaryCategorySlugs.join(',') : primaryCategorySlug!;
      const isValid = products.length >= minProducts;
      onValidation(identifier, isValid, slot);
      validationCalled.current = true;
    }
  }, [isFetched, products, onValidation, primaryCategorySlug, primaryCategorySlugs, slot, minProducts]);


  // If loading is done and it's invalid, render nothing.
  if (!isLoading && products.length < minProducts) {
    return null;
  }

  if (isLoading) {
    return (
      <section className="bg-muted p-8 rounded-lg">
        <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold">
          <span className="bg-yellow-300 px-0.5 py-1 rounded italic text-black">{title}</span>
        </h2>
          {searchQuery && (
            <Link to={`/search?q=${encodeURIComponent(searchQuery)}`} className="text-sm text-blue-500 hover:underline">
              See more
            </Link>
          )}
        </div>
        <div className="overflow-x-auto pb-4">
          <div className="flex">
            {[...Array(5)].map((_, i) => (
              <div className="flex-shrink-0 w-1/2 sm:w-1/3 md:w-1/4 lg:w-1/5 px-2 pb-2" key={i}>
                <SkeletonProductTile />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error.message}</div>;
  }

  let seeMoreLink = null;
  if (primaryCategorySlugs) {
    if (primaryCategorySlugs.length > 1 && pillarPageLinkSlug) {
      // Home page case: multiple slugs, link to the pillar page
      seeMoreLink = `/categories/${encodeURIComponent(pillarPageLinkSlug)}`;
    } else if (primaryCategorySlugs.length === 1) {
      // Pillar page case: single slug, link to a search for that primary category
      seeMoreLink = `/search?primary_category_slug=${encodeURIComponent(primaryCategorySlugs[0])}`;
    } else {
      // Fallback for multiple slugs but no pillarPageLinkSlug, or other edge cases
      seeMoreLink = `/search?primary_category_slugs=${encodeURIComponent(primaryCategorySlugs.join(','))}`;
    }
  } else if (primaryCategorySlug) {
    // Fallback for the old singular prop
    seeMoreLink = `/search?primary_category_slug=${encodeURIComponent(primaryCategorySlug)}`;
  }

  return (
    <>
      <section className="bg-muted p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">
            <span className="bg-yellow-300 px-0.5 py-1 rounded italic text-black">{title}</span>
          </h2>
          {isDefaultStores && (
            <span className="ml-2 text-sm text-muted-foreground bg-blue-100 px-2 py-1 rounded-md">
              Showing example products, please select a location.
            </span>
          )}
          {seeMoreLink && (
            <Link to={seeMoreLink} className="text-sm text-blue-500 hover:underline">
              See more
            </Link>
          )}
        </div>
        <div className="overflow-x-auto pb-4">
          <div className="flex">
            {products?.map((product) => (
              <div className="flex-shrink-0 w-1/2 sm:w-1/3 md:w-1/4 lg:w-1/5 px-2 pb-2" key={product.id}>
                <ProductTile product={product} />
              </div>
            ))}
          </div>
        </div>
      </section>
      {products.length > 0 && <JsonLdItemList products={products} title={title} />}
    </>
  );
};

export const ProductCarousel = memo(ProductCarouselComponent);
