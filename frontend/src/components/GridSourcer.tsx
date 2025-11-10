import React, { useState } from 'react';
import ProductGrid from './ProductGrid';
import type { Product } from '../types'; // Import shared type

import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "./ui/pagination";

import { useStoreList } from '../context/StoreListContext';
import LoadingSpinner from './LoadingSpinner';

// Type for the API response, using the shared Product type
type ApiResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
};

interface GridSourcerProps {
  searchTerm: string | null;
  sourceUrl: string | null;
  primaryCategorySlug: string | null;
}

import { useApiQuery } from '../hooks/useApiQuery';

const GridSourcer: React.FC<GridSourcerProps> = ({ searchTerm, sourceUrl, primaryCategorySlug }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const { selectedStoreIds } = useStoreList(); // Get selected stores

  // Determine API endpoint and params
  const { url, params } = React.useMemo(() => {
    const params = new URLSearchParams();
    let url = '';

    if (sourceUrl) {
      const [baseUrl, queryString] = sourceUrl.split('?');
      url = baseUrl;
      const existingParams = new URLSearchParams(queryString || '');
      existingParams.forEach((value, key) => params.set(key, value));
    } else if (searchTerm) {
      url = '/api/products/';
      params.set('search', searchTerm);
    } else if (primaryCategorySlug) {
      url = '/api/products/';
      params.set('primary_category_slug', primaryCategorySlug);
    }

    if (selectedStoreIds && selectedStoreIds.size > 0) {
      params.set('store_ids', Array.from(selectedStoreIds).join(','));
    }
    params.set('page', currentPage.toString());
    params.set('page_size', '20');

    return { url, params };
  }, [searchTerm, sourceUrl, primaryCategorySlug, selectedStoreIds, currentPage]);

  const finalUrl = url ? `${url}?${params.toString()}` : null;

  const { 
    data: apiResponse,
    isLoading,
    isError,
    error,
  } = useApiQuery<ApiResponse>(
    ['products', finalUrl],
    finalUrl || '',
    {},
    { enabled: !!finalUrl }
  );

  const products = apiResponse?.results || [];
  const totalResults = apiResponse?.count || 0;
  const totalPages = Math.ceil(totalResults / 20); // Assuming 20 results per page


  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  let titleText = "";
  if (searchTerm) {
    titleText = `Found ${totalResults} results for "${searchTerm}"`;
  } else if (primaryCategorySlug) {
    const formattedSlug = primaryCategorySlug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    titleText = `Showing ${totalResults} products in "${formattedSlug}"`;
  } else if (sourceUrl) {
    // Basic title for sourceUrl, can be improved
    titleText = `Showing ${totalResults} products`;
  } else if (products.length === 0) {
    titleText = "Please enter a search to begin.";
  }

  if (isLoading) {
    return <LoadingSpinner fullScreen={false} />;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error.message}</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">{titleText}</h2>
      <ProductGrid 
        products={products} 
      />
      <div className="flex justify-center mt-8">
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious 
                href="#" 
                onClick={() => handlePageChange(currentPage - 1)} 
                className={currentPage === 1 ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>
            {
              (() => {
                const paginationItems = [];
                const siblings = 1;
                const boundaries = 1;

                if (totalPages <= 5) {
                  for (let i = 1; i <= totalPages; i++) {
                    paginationItems.push(i);
                  }
                } else {
                  paginationItems.push(1);
                  if (currentPage > siblings + boundaries + 1) {
                    paginationItems.push('ellipsis-start');
                  }

                  const startPage = Math.max(2, currentPage - siblings);
                  const endPage = Math.min(totalPages - 1, currentPage + siblings);

                  for (let i = startPage; i <= endPage; i++) {
                    paginationItems.push(i);
                  }

                  if (currentPage < totalPages - siblings - boundaries - 1) {
                    paginationItems.push('ellipsis-end');
                  }
                  paginationItems.push(totalPages);
                }

                return paginationItems.map((item, i) => (
                  <PaginationItem key={i}>
                    {typeof item === 'number' ? (
                      <PaginationLink
                        href="#"
                        onClick={() => handlePageChange(item)}
                        isActive={currentPage === item}
                      >
                        {item}
                      </PaginationLink>
                    ) : (
                      <PaginationEllipsis />
                    )}
                  </PaginationItem>
                ));
              })()
            }
            <PaginationItem>
              <PaginationNext 
                href="#" 
                onClick={() => handlePageChange(currentPage + 1)} 
                className={currentPage === totalPages ? "pointer-events-none opacity-50" : ""}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      </div>
    </div>
  );
};

export default GridSourcer;