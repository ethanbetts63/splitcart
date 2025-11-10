import React from 'react';
import ProductTile from './ProductTile';
import type { Product } from '../types'; // Import shared type

interface ProductGridProps {
  products: Product[];
  hasResults: boolean;
}

const ProductGrid: React.FC<ProductGridProps> = ({ 
  products, 
  hasResults,
}) => {
  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {products.length > 0 ? (
          products.map((product) => (
            <ProductTile key={product.id} product={product} />
          ))
        ) : null}
      </div>
    </div>
  );
};

export default ProductGrid;