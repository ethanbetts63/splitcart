import React from 'react';
import { Card } from "@/components/ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '@/assets/splitcart_symbol_v6.png';
import type { Product } from '@/types/Product'; // Import shared type

import { Button } from '@/components/ui/button';

interface TrolleyItemTileProps {
  product: Product;
  onApprove?: (product: Product) => void;
  isApproved?: boolean;
}

import { Badge } from "@/components/ui/badge";

const TrolleyItemTile: React.FC<TrolleyItemTileProps> = ({ product, onApprove, isApproved }) => {

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const imageUrl = product.image_url || fallbackImage;

  return (
    <Card className="p-2 flex flex-row items-center gap-4 relative">
      {product.substitution_level && (
        <Badge variant="secondary" className="absolute top-2 left-2 z-10 bg-blue-500 text-white dark:bg-blue-600">{product.substitution_level}</Badge>
      )}
      {/* Image */}
      <div className="w-16 h-16 flex-shrink-0">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover rounded-md"
        />
      </div>

      {/* Middle Section: Info & Price */}
      <div className="flex-grow grid gap-1 justify-items-center">
        <p className="font-semibold line-clamp-1">{product.name}</p>
        {product.size && <Badge variant="default">{product.size}</Badge>}
        <PriceDisplay prices={product.prices} />
      </div>

      {/* Right Section: Quantity Controls */}
      <div className="flex-shrink-0">
        {onApprove ? (
          <Button onClick={() => onApprove(product)} variant={isApproved ? 'destructive' : 'outline'}>
            {isApproved ? 'Remove' : 'Approve'}
          </Button>
        ) : (
          <AddToCartButton product={product} />
        )}
      </div>
    </Card>
  );
};

export default TrolleyItemTile;