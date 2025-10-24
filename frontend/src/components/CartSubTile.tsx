import React from 'react';
import { Card } from "@/components/ui/card";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from "@/components/ui/badge";
import fallbackImage from '@/assets/splitcart_symbol_v6.png';
import type { Product } from '@/types';

interface CartSubTileProps {
  product: Product; // We'll use a dummy product
  quantity: number;
}

const CartSubTile: React.FC<CartSubTileProps> = ({ product, quantity }) => {
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const imageUrl = product.image_url || fallbackImage;

  return (
    <div className="p-2 flex items-center gap-2 border-t">
      {/* Image */}
      <div className="w-12 h-12 flex-shrink-0">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover rounded-md"
        />
      </div>

      {/* Middle Section: Info */}
      <div className="flex-grow grid grid-cols-3 items-center">
        <p className="font-semibold line-clamp-1 col-span-1">{product.name}</p>
        <p className="text-sm text-muted-foreground col-span-1">{product.brand_name}</p>
        {product.size && <Badge variant="outline" className="w-fit col-span-1">{product.size}</Badge>}
      </div>

      {/* Right Section: Quantity Controls */}
      <div className="flex-shrink-0 flex items-center gap-2">
        <Button size="icon" className="h-6 w-6">-</Button>
        <Input
          type="number"
          readOnly
          className="h-6 w-10 text-center no-spinner"
          value={quantity}
          min="0"
        />
        <Button size="icon" className="h-6 w-6">+</Button>
      </div>
    </div>
  );
};

export default CartSubTile;
