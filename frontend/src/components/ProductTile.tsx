import React from 'react';
import { cn } from '@/lib/utils';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '@/assets/splitcart_symbol_v6.png';

import { Badge } from "@/components/ui/badge";
import { Product } from '@/types/Product'; // Import shared type

interface ProductTileProps {
  product: Product;
}

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  // The API now provides a deterministic image_url for the product.
  const imageUrl = product.image_url || fallbackImage;

  return (
    <Card className="w-full flex flex-col h-full overflow-hidden gap-3 pt-0">
      <div className="aspect-square w-full overflow-hidden relative">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover transition-transform"
        />
        {product.size && (
          <Badge className="absolute top-2 right-2">{product.size}</Badge>
        )}
      </div>
      <CardHeader className="p-0 pb-0 text-center">
        <CardTitle className="h-12 line-clamp-2 text-base">{product.name}</CardTitle>
        {product.brand_name && <CardDescription>{product.brand_name}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-grow p-0">
        <PriceDisplay prices={product.prices} />
      </CardContent>
      <CardFooter className="flex justify-center p-0 pt-0">
        <AddToCartButton product={product} />
      </CardFooter>
    </Card>
  );
};

export default ProductTile;