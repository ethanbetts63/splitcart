import React, { useState, useEffect } from 'react';
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
import fallbackImage from '@/assets/splitcart_symbol_v6.png';

// Define the types for our product data based on the old component
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

interface ProductTileProps {
  product: Product;
}

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {
  const [selectedPrice, setSelectedPrice] = useState<Price | null>(null);

  useEffect(() => {
    const prices = product.prices || [];
    const cheapestPrice = prices.find(p => p.is_lowest) || 
                          (prices.length > 0 ? prices.reduce((min, p) => parseFloat(p.price) < parseFloat(min.price) ? p : min, prices[0]) : null);
    setSelectedPrice(cheapestPrice);
  }, [product.prices]);

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const imageUrl = selectedPrice?.image_url || product.image_url || fallbackImage;

  return (
    <Card className="w-full flex flex-col h-full overflow-hidden">
      <div className="aspect-square w-full overflow-hidden">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover transition-transform hover:scale-105"
        />
      </div>
      <CardHeader>
        <CardTitle className="h-12 line-clamp-2 text-base">{product.name}</CardTitle>
        {product.brand_name && <CardDescription>{product.brand_name}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-grow">
        {/* PriceDisplay would go here */}
        <p className="text-lg font-semibold">
          {selectedPrice ? `$${selectedPrice.price}` : 'Price not available'}
        </p>
      </CardContent>
      <CardFooter className="flex justify-center">
        <AddToCartButton product={product} />
      </CardFooter>
    </Card>
  );
};

export default ProductTile;