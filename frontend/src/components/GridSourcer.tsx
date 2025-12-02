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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

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
  primaryCategorySlugs?: string | null;
  bargainCompany?: string | null;
}

import { useApiQuery } from '../hooks/useApiQuery';
import { useAuth } from '../context/AuthContext';
import { useQueryClient } from '@tanstack/react-query';

const GridSourcer: React.FC<GridSourcerProps> = ({ searchTerm, sourceUrl, primaryCategorySlug, primaryCategorySlugs, bargainCompany }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortOption, setSortOption] = useState('');
  const { selectedStoreIds } = useStoreList(); // Get selected stores
  const queryClient = useQueryClient();
  const { token, anonymousId } = useAuth();

  // Determine API endpoint and params
  const { url, params } = React.useMemo(() => {
    const params = new URLSearchParams();
    let url = '';

    if (bargainCompany) {
      url = '/api/products/';
      params.set('bargain_company', bargainCompany);
    } else if (sourceUrl) {
      const [baseUrl, queryString] = sourceUrl.split('?');
      url = baseUrl;
      const existingParams = new URLSearchParams(queryString || '');
      existingParams.forEach((value, key) => params.set(key, value));
    } else if (searchTerm) {
      url = '/api/products/';
      params.set('search', searchTerm);
    } else if (primaryCategorySlugs) {
      url = '/api/products/';
      params.set('primary_category_slugs', primaryCategorySlugs);
    }
    else if (primaryCategorySlug) {
      url = '/api/products/';
      params.set('primary_category_slug', primaryCategorySlug);
    }

    if (selectedStoreIds && selectedStoreIds.size > 0) {
      params.set('store_ids', Array.from(selectedStoreIds).join(','));
    }
    params.set('page', currentPage.toString());
    params.set('page_size', '20');

    if (sortOption) {
      params.set('ordering', sortOption);
    }

    return { url, params };
  }, [searchTerm, sourceUrl, primaryCategorySlug, primaryCategorySlugs, selectedStoreIds, currentPage, sortOption, bargainCompany]);

  const finalUrl = url ? `${url}?${params.toString()}` : null;

  const { 
    data: apiResponse,
    isLoading,
  } = useApiQuery<ApiResponse>(
    ['products', finalUrl],
    finalUrl || '',
    {},
    { enabled: !!finalUrl }
  );

  // Prefetch the next page
  React.useEffect(() => {
    if (apiResponse?.next) {
      const nextPage = currentPage + 1;
      const nextParams = new URLSearchParams(params);
      nextParams.set('page', nextPage.toString());
      
      // Ensure the URL starts with /api/
      const nextUrlPath = url.startsWith('/api') ? url : `/api${url.substring(1)}`;
      const nextFinalUrl = `${nextUrlPath}?${nextParams.toString()}`;

      const nextQueryKey = ['products', nextFinalUrl];

      queryClient.prefetchQuery({
        queryKey: nextQueryKey,
        queryFn: async () => {
          const headers: Record<string, string> = {
            'Content-Type': 'application/json',
          };
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          } else if (anonymousId) {
            headers['X-Anonymous-ID'] = anonymousId;
          }
          const response = await fetch(nextFinalUrl, { headers });
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        },
      });
    }
  }, [apiResponse, currentPage, params, url, queryClient, token, anonymousId]);

  const products = apiResponse?.results || [];
  const totalResults = apiResponse?.count || 0;
  const totalPages = Math.ceil(totalResults / 20); // Assuming 20 results per page


  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen={false} />;
  }

    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">
            {bargainCompany && (
              <>
                Showing {totalResults} bargains for{" "}
                <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">
                  "{bargainCompany}"
                </span>
              </>
            )}
            {searchTerm && (
              <>
                Found {totalResults} results for{" "}
                <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">
                  "{searchTerm}"
                </span>
              </>
            )}
            {primaryCategorySlug && !searchTerm && (
              (() => {
                const formattedSlug = primaryCategorySlug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <>
                    Showing {totalResults} products in{" "}
                    <span className="font-bold bg-yellow-300 px-0.5 py-1 rounded italic text-black">
                      "{formattedSlug}"
                    </span>
                  </>
                );
              })()
            )}
            {sourceUrl && !searchTerm && !primaryCategorySlug && !bargainCompany && (
              <>
                Showing {totalResults} products
              </>
            )}
          </h2>
          <div className="flex items-center">
            {!bargainCompany && (
              <Select onValueChange={(value) => setSortOption(value)} value={sortOption}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default</SelectItem>
                  <SelectItem value="price_asc">Price: Low to High</SelectItem>
                  <SelectItem value="price_desc">Price: High to Low</SelectItem>
                  <SelectItem value="unit_price_asc">Per Unit Price: Low to High</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
        <ProductGrid 
          products={products} 
          hasResults={totalResults > 0}
        />
        {totalResults > 0 && (
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
        )}
      </div>
    );
  };
export default GridSourcer;