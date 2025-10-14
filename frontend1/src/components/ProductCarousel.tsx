import React, { useState, useEffect } from 'react';
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

interface ProductCarouselProps {
  sourceUrl: string;
  storeIds?: number[]; // Make storeIds an optional prop
}

export const ProductCarousel: React.FC<ProductCarouselProps> = ({ sourceUrl, storeIds }) => {
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
    return <div className="text-center p-4">Loading...</div>;
  }

  if (error) {
    return <div className="text-center p-4 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="custom-carousel">
      <div className="custom-carousel__container">
        {products.map((product) => (
          <div className="custom-carousel__slide" key={product.id}>
            <ProductTile product={product} />
          </div>
        ))}
      </div>
    </div>
  );
}
