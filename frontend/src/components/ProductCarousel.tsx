import React, { memo, useEffect, useRef } from 'react';
import SkeletonProductTile from "./SkeletonProductTile";
import ProductTile from "./ProductTile";
import { Link, useLocation } from 'react-router-dom';
import type { Product } from '../types';
import JsonLdItemList from './JsonLdItemList';
import { ArrowRight } from 'lucide-react';

interface ProductCarouselProps {
  sourceUrl?: string;
  products?: Product[];
  storeIds?: number[];
  title: string;
  searchQuery?: string;
  isDefaultStores?: boolean;
  isUserDefinedList?: boolean;
  primaryCategorySlug?: string;
  primaryCategorySlugs?: string[];
  pillarPageLinkSlug?: string;
  companyName?: string;
  isBargainCarousel?: boolean;
  onValidation?: (slug: string, isValid: boolean, slot: number) => void;
  slot?: number;
  dataKey?: string;
  minProducts?: number;
  ordering?: string;
  isLoading?: boolean;
}

import { useApiQuery } from '@/hooks/useApiQuery';
import { useDialog } from '@/context/DialogContext';

const ProductCarouselComponent: React.FC<ProductCarouselProps> = ({
  sourceUrl,
  products: initialProducts,
  storeIds,
  title,
  searchQuery,
  isDefaultStores,
  isUserDefinedList,
  primaryCategorySlug,
  primaryCategorySlugs,
  pillarPageLinkSlug,
  companyName,
  isBargainCarousel,
  onValidation,
  slot,
  dataKey,
  minProducts = 4,
  ordering,
  isLoading: isLoadingProp,
}) => {
  const { openDialog } = useDialog();
  const [isSmallScreen, setIsSmallScreen] = React.useState(false);
  const location = useLocation();

  React.useEffect(() => {
    const handleResize = () => {
      setIsSmallScreen(window.innerWidth < 750);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const finalUrl = React.useMemo(() => {
    const [baseUrl, queryString] = sourceUrl ? sourceUrl.split('?') : ['', ''];
    const params = new URLSearchParams(queryString || '');
    if (isUserDefinedList && storeIds && storeIds.length > 0) {
      params.set('store_ids', storeIds.join(','));
    }
    if (primaryCategorySlugs && primaryCategorySlugs.length > 0) {
      params.set('primary_category_slugs', primaryCategorySlugs.join(','));
    } else if (primaryCategorySlug) {
      params.set('primary_category_slug', primaryCategorySlug);
    }
    if (companyName) {
      params.set('company_name', companyName);
    }
    if (sourceUrl && !sourceUrl.includes('substitutes')) {
      params.set('limit', '20');
      if (ordering) {
        params.set('ordering', ordering);
      } else if (!params.has('ordering')) {
        params.set('ordering', 'carousel_default');
      }
    }
    return sourceUrl ? `${baseUrl}?${params.toString()}` : '';
  }, [sourceUrl, storeIds, isUserDefinedList, primaryCategorySlugs, primaryCategorySlug, companyName, ordering]);

  const { data: responseData, isLoading: isFetching, error, isFetched } = useApiQuery<any>(
    ['products', title, finalUrl],
    finalUrl,
    {},
    { enabled: !!finalUrl && !initialProducts, refetchOnWindowFocus: false, staleTime: 1000 * 60 * 10 }
  );

  const products: Product[] = React.useMemo(() => {
    if (initialProducts) return initialProducts;
    if (!responseData) return [];
    const results = Array.isArray(responseData) ? responseData : responseData.results || [];
    if (dataKey) {
      return results.map((item: any) => item[dataKey]).filter(Boolean);
    }
    return results;
  }, [initialProducts, responseData, dataKey]);

  const validationCalled = useRef(false);
  useEffect(() => {
    if (isFetched && onValidation && (primaryCategorySlug || primaryCategorySlugs) && !validationCalled.current && slot !== undefined) {
      const identifier = primaryCategorySlugs ? primaryCategorySlugs.join(',') : primaryCategorySlug!;
      const isValid = products.length >= minProducts;
      onValidation(identifier, isValid, slot);
      validationCalled.current = true;
    }
  }, [isFetched, products, onValidation, primaryCategorySlug, primaryCategorySlugs, slot, minProducts]);

  const isLoading = (isLoadingProp ?? isFetching) && !initialProducts;

  if (!isLoading && products.length < minProducts) return null;
  if (error) return <div className="text-center p-4 text-red-500">Error: {error.message}</div>;

  // --- See More Link ---
  let seeMoreLink = null;
  if (isBargainCarousel && companyName) {
    seeMoreLink = `/search?bargain_company=${encodeURIComponent(companyName)}`;
  } else if (pillarPageLinkSlug && location.pathname === '/') {
    seeMoreLink = `/categories/${encodeURIComponent(pillarPageLinkSlug)}`;
  } else if (primaryCategorySlugs && primaryCategorySlugs.length > 0) {
    seeMoreLink = primaryCategorySlugs.length === 1
      ? `/search?primary_category_slug=${encodeURIComponent(primaryCategorySlugs[0])}`
      : `/search?primary_category_slugs=${encodeURIComponent(primaryCategorySlugs.join(','))}`;
  } else if (primaryCategorySlug) {
    seeMoreLink = `/search?primary_category_slug=${encodeURIComponent(primaryCategorySlug)}`;
  } else if (searchQuery) {
    seeMoreLink = `/search?q=${encodeURIComponent(searchQuery)}`;
  }

  const exploreHref = seeMoreLink ?? (title === 'Bargains' ? '/bargains' : null);
  const exploreLabel = isBargainCarousel && companyName
    ? `Explore All ${companyName} Deals`
    : title === 'Bargains'
    ? 'Explore More Bargains'
    : 'Explore All Deals';

  return (
    <>
      <section className="bg-gray-50 p-5 rounded-xl">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4 pb-3 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold">
              <span className="bg-yellow-300 px-0.5 py-1 rounded italic text-black">{title}</span>
            </h2>
            {isDefaultStores && !isLoading && (
              <p className="text-sm text-gray-500 mt-1.5">
                Showing example products —{' '}
                <button
                  onClick={() => openDialog('Edit Location')}
                  className="text-blue-600 underline hover:text-blue-800"
                >
                  select a location
                </button>
              </p>
            )}
          </div>
          {exploreHref && (
            <Link
              to={exploreHref}
              aria-label={exploreLabel}
              className="shrink-0 flex items-center gap-1.5 text-sm font-semibold text-gray-700 border border-gray-300 bg-white hover:border-gray-900 hover:text-gray-900 px-3 py-1.5 rounded-lg transition-colors duration-150"
            >
              {isSmallScreen ? 'Explore' : exploreLabel}
              <ArrowRight className="h-4 w-4" />
            </Link>
          )}
        </div>

        {/* Tiles */}
        <div className="overflow-x-auto scrollbar-hide pb-1 pt-2">
          <div className="flex snap-x snap-mandatory">
            {isLoading
              ? [...Array(5)].map((_, i) => (
                  <div className="flex-shrink-0 snap-start w-4/5 sm:w-1/3 md:w-1/4 lg:w-1/5 px-1.5 pb-1" key={i}>
                    <SkeletonProductTile />
                  </div>
                ))
              : products.map((product) => (
                  <div className="flex-shrink-0 snap-start w-4/5 sm:w-1/3 md:w-1/4 lg:w-1/5 px-1.5 pb-1" key={product.id}>
                    <ProductTile product={product} />
                  </div>
                ))
            }
          </div>
        </div>
      </section>
      {!isLoading && products.length > 0 && <JsonLdItemList products={products} title={title} />}
    </>
  );
};

export const ProductCarousel = memo(ProductCarouselComponent);
