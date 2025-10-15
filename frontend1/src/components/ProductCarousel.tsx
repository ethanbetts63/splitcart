import React, { useState, useEffect } from 'react';
import { Skeleton } from "@/components/ui/skeleton";
import SkeletonProductTile from "./SkeletonProductTile";
import ProductTile from "./ProductTile";
import '../css/ProductCarousel.css';

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

import { Link } from 'react-router-dom';

interface ProductCarouselProps {
  sourceUrl: string;
  storeIds?: number[]; // Make storeIds an optional prop
  title: string;
  searchQuery?: string;
}

export const ProductCarousel: React.FC<ProductCarouselProps> = ({ sourceUrl, storeIds, title, searchQuery }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProducts = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Separate URL and existing params
        const [baseUrl, queryString] = sourceUrl.split('?');
        const params = new URLSearchParams(queryString || '');

        // Add store_ids if they are provided
        if (storeIds && storeIds.length > 0) {
          params.append('store_ids', storeIds.join(','));
        }

        const finalUrl = `${baseUrl}?${params.toString()}`;

        const response = await fetch(finalUrl);
        if (!response.ok) {
          throw new Error('Failed to fetch products');
        }
        const data: ApiResponse = await response.json();
        setProducts(data.results || []);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, [sourceUrl, storeIds]); // Add storeIds to dependency array

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
        <div className="custom-carousel">
          <div className="custom-carousel__container">
            {[...Array(5)].map((_, i) => (
              <div className="custom-carousel__slide" key={i}>
                <SkeletonProductTile />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error}</div>;
  }

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
      <div className="custom-carousel">
      <div className="custom-carousel__container">
        {products.map((product) => (
          <div className="custom-carousel__slide" key={product.id}>
            <ProductTile product={product} />
          </div>
        ))}
      </div>
    </div>
    </div>
  );
}
