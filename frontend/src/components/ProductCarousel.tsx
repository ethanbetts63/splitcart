import React, { memo } from 'react';
import SkeletonProductTile from "./SkeletonProductTile";
import ProductTile from "./ProductTile";
import { Link } from 'react-router-dom';

// --- Type Definitions ---
type CompanyPriceInfo = {
  company: string;
  price_display: string;
  is_lowest: boolean;
  image_url?: string;
};

type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: CompanyPriceInfo[];
};

type ApiResponse = {
  results: Product[];
};

interface ProductCarouselProps {
  sourceUrl: string;
  storeIds?: number[];
  title: string;
  searchQuery?: string;
  isDefaultStores?: boolean; // New prop
}

import { useApiQuery } from '@/hooks/useApiQuery';

const ProductCarouselComponent: React.FC<ProductCarouselProps> = ({ sourceUrl, storeIds, title, searchQuery, isDefaultStores }) => {
  const [baseUrl, queryString] = sourceUrl.split('?');
  const params = new URLSearchParams(queryString || '');
  if (storeIds && storeIds.length > 0) {
    params.set('store_ids', storeIds.join(','));
  }

  const finalUrl = `${baseUrl}?${params.toString()}`;

  const { data: apiResponse, isLoading, error } = useApiQuery<ApiResponse>(
    ['products', title, finalUrl],
    finalUrl,
    {},
    { enabled: !!storeIds && storeIds.length > 0 }
  );

  const products = apiResponse?.results || [];

  if (isLoading) {
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">{title}</h2>
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
      </div>
    );
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error.message}</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">{title}</h2>
        {isDefaultStores && (
          <span className="ml-2 text-sm text-muted-foreground bg-blue-100 px-2 py-1 rounded-md">
            Showing example products, please select a location.
          </span>
        )}
        {searchQuery && (
          <Link to={`/search?q=${encodeURIComponent(searchQuery)}`} className="text-sm text-blue-500 hover:underline">
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
    </div>
  );
};

export const ProductCarousel = memo(ProductCarouselComponent);
