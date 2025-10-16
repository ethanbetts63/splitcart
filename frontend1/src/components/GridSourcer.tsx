import React, { useState, useEffect, useCallback } from 'react';
import ProductGrid from './ProductGrid';
import type { Product } from '@/types/Product'; // Import shared type

import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

import { useStoreSelection } from '@/context/StoreContext';

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
}

const GridSourcer: React.FC<GridSourcerProps> = ({ searchTerm, sourceUrl }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const { selectedStoreIds } = useStoreSelection(); // Get selected stores

  const fetchProducts = useCallback(async (page: number) => {
    setIsLoading(true);
    setIsError(false);
    setError(null);

    let url = '';
    const params = new URLSearchParams();

    if (sourceUrl) {
      url = sourceUrl;
    } else if (searchTerm) {
      url = '/api/products/';
      params.append('search', searchTerm);
    } else {
      setIsLoading(false);
      setProducts([]);
      setTotalResults(0);
      return;
    }

    // Add store_ids if they are provided
    if (selectedStoreIds && selectedStoreIds.size > 0) {
      params.append('store_ids', Array.from(selectedStoreIds).join(','));
    }

    params.append('page', page.toString());

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    try {
      const response = await fetch(url);
      if (!response.ok) {
        let errorMessage = `Failed to fetch: ${response.statusText}`;
        try {
            const errData = await response.json();
            errorMessage = errData.detail || errData.error || errorMessage;
        } catch (e) {
            // Response was not JSON, stick with the status text
        }
        throw new Error(errorMessage);
      }
      const data: ApiResponse = await response.json();
      
      const productList = data.results || [];
      const count = data.count;

      setProducts(productList);
      setTotalResults(count);
      setTotalPages(Math.ceil(count / 20)); // Assuming 20 results per page

    } catch (e: any) {
      setIsError(true);
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, sourceUrl, selectedStoreIds]);

  // Effect for fetching data when page or search term changes
  useEffect(() => {
    fetchProducts(currentPage);
  }, [currentPage, fetchProducts]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  let titleText = "";
  if (searchTerm) {
    titleText = `Found ${totalResults} results for "${searchTerm}"`;
  } else if (sourceUrl) {
    // Basic title for sourceUrl, can be improved
    titleText = `Showing ${totalResults} products`;
  } else if (products.length === 0) {
    titleText = "Please enter a search to begin.";
  }

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error}</div>;
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