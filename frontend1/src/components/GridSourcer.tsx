import React, { useState, useEffect, useCallback } from 'react';
import ProductGrid from './ProductGrid';

// Define the types for our product data again
// In a real app, these would be in a shared types file
type Price = {
  id: number;
  price: string;
  store_id: number;
  is_lowest: boolean;
  image_url?: string;
};

type Product = {
  id: number;
  name: string;
  brand_name?: string;
  size?: string;
  image_url?: string;
  prices: Price[];
};

interface GridSourcerProps {
  searchTerm: string | null;
  sourceUrl: string | null;
}

// --- MOCK DATA --- //
const createMockProduct = (id: number): Product => ({
  id,
  name: `Product Name ${id}`,
  brand_name: `Brand ${id}`,
  size: `${id * 100}g`,
  image_url: `https://picsum.photos/seed/${id}/300/300`,
  prices: [
    {
      id: id * 100 + 1,
      price: (10 - id * 0.5).toFixed(2),
      store_id: 1,
      is_lowest: true,
    },
  ],
});

const mockProducts: Product[] = Array.from({ length: 20 }, (_, i) => createMockProduct(i + 1));
// --- END MOCK DATA --- //

const GridSourcer: React.FC<GridSourcerProps> = ({ searchTerm, sourceUrl }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);

  // The real data fetching logic is temporarily disabled to focus on UI.
  useEffect(() => {
    setIsLoading(true);
    // Simulate a network request
    const timer = setTimeout(() => {
      setProducts(mockProducts);
      setTotalResults(mockProducts.length);
      setIsLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm, sourceUrl]);

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  if (isError) {
    return <div className="text-center p-8 text-red-500">Error: {error}</div>;
  }

  let titleText = "";
  if (searchTerm) {
    titleText = `Found ${totalResults} results for "${searchTerm}"`;
  } else {
    titleText = `Showing ${totalResults} products`;
  }

  return (
    <ProductGrid 
      products={products} 
      onLoadMore={() => {}} // No-op for now
      hasMorePages={false} // No pagination with mock data
      isLoadingMore={false}
      title={titleText}
    />
  );
};

export default GridSourcer;