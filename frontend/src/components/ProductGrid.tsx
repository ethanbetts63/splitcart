import React from 'react';
import ProductTile from './ProductTile';
import { Button } from '@/components/ui/button';
import type { Product } from '@/types'; // Import shared type

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