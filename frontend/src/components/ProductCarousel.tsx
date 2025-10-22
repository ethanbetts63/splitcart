import React, { memo } from 'react';
import { useQuery } from '@tanstack/react-query';
import SkeletonProductTile from "./SkeletonProductTile";
import ProductTile from "./ProductTile";
import '../css/ProductCarousel.css';
import { useAuth } from '@/context/AuthContext';
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
}

const fetchProducts = async (sourceUrl: string, storeIds: number[] | undefined, token: string | null): Promise<Product[]> => {
  const [baseUrl, queryString] = sourceUrl.split('?');
  const params = new URLSearchParams(queryString || '');

  if (storeIds && storeIds.length > 0) {
    params.append('store_ids', storeIds.join(','));
  }

  const finalUrl = `http://127.0.0.1:8000${baseUrl}?${params.toString()}`;

  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Token ${token}`;
  }

  const response = await fetch(finalUrl, { headers });
  if (!response.ok) {
    throw new Error('Failed to fetch products');
  }
  const data: ApiResponse = await response.json();
  return data.results || [];
};

const ProductCarouselComponent: React.FC<ProductCarouselProps> = ({ sourceUrl, storeIds, title, searchQuery }) => {
  const { token } = useAuth();

  const { data: products, isLoading, error } = useQuery<Product[], Error>({
    queryKey: ['products', title, sourceUrl, storeIds],
    queryFn: () => fetchProducts(sourceUrl, storeIds, token),
  });

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
    return <div className="text-center p-4 text-red-500">Error: {error.message}</div>;
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
          {products?.map((product) => (
            <div className="custom-carousel__slide" key={product.id}>
              <ProductTile product={product} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export const ProductCarousel = memo(ProductCarouselComponent);
