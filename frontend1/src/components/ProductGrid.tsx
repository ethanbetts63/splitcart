import React from 'react';
import ProductTile from './ProductTile';
import { Button } from '@/components/ui/button';

// Define the types for our product data again for this component
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

interface ProductGridProps {
  products: Product[];
  onLoadMore: () => void;
  hasMorePages: boolean;
  isLoadingMore: boolean;
  title?: string;
}

const ProductGrid: React.FC<ProductGridProps> = ({ 
  products, 
  onLoadMore, 
  hasMorePages, 
  isLoadingMore, 
  title 
}) => {
  return (
    <div>
      {title && <h2 className="text-2xl font-bold mb-4">{title}</h2>}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {products.length > 0 ? (
          products.map((product) => (
            <ProductTile key={product.id} product={product} />
          ))
        ) : (
          <div className="col-span-full text-center py-8">
            <p>No products found.</p>
          </div>
        )}
      </div>

      {hasMorePages && (
        <div className="text-center my-8">
          <Button onClick={onLoadMore} disabled={isLoadingMore}>
            {isLoadingMore ? 'Loading...' : 'Load More'}
          </Button>
        </div>
      )}
    </div>
  );
};

export default ProductGrid;
