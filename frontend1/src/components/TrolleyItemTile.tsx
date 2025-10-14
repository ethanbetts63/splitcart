import React from 'react';
import { Card } from "@/components/ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '@/assets/splitcart_symbol_v6.png';

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
  image_url?: string;
  prices: CompanyPriceInfo[];
};

interface TrolleyItemTileProps {
  product: Product;
}

const TrolleyItemTile: React.FC<TrolleyItemTileProps> = ({ product }) => {

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
        <AddToCartButton product={product} />
      </div>
    </Card>
  );
};

export default TrolleyItemTile;
