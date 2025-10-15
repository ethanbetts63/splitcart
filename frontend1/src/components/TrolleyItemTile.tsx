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

const TrolleyItemTile: React.FC<TrolleyItemTileProps> = ({ product, onApprove, isApproved }) => {

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const imageUrl = product.image_url || fallbackImage;

  return (
    <Card className="p-2 flex flex-row items-center gap-4">
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
      <div className="flex-grow grid gap-1">
        <p className="font-semibold line-clamp-1">{product.name}</p>
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