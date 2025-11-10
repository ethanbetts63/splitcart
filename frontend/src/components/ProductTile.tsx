import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';

import { Badge } from "./ui/badge";
import type { Product } from '../types'; // Import shared type

interface ProductTileProps {
  product: Product;
}

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {
  const [imageUrl, setImageUrl] = useState(product.image_url || fallbackImage);

  // Effect to reset the image URL when the product prop changes
  useEffect(() => {
    setImageUrl(product.image_url || fallbackImage);
  }, [product.image_url]);

  const handleImageError = () => {
    // Prevent a loop if the fallback image itself is broken
    if (imageUrl !== fallbackImage) {
      setImageUrl(fallbackImage);
    }
  };

  const generateSrcSet = (url: string) => {
    if (!url.includes('cdn.metcash.media')) {
      return undefined;
    }
    const sizes = [200, 250, 300, 350, 400, 450, 500];
    return sizes
      .map(size => `${url.replace('w_1500,h_1500', `w_${size},h_${size},f_auto`)} ${size}w`)
      .join(', ');
  };

  const srcSet = generateSrcSet(imageUrl);

  return (
    <Card className="flex flex-col h-full overflow-hidden gap-1 pt-0 pb-2">
      <div className="aspect-square w-full overflow-hidden relative">
        <img
          src={imageUrl}
          srcSet={srcSet}
          sizes="273px"
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover transition-transform hover:scale-105"
        />
        {product.size && (
          <Badge className="absolute top-2 right-2">{product.size}</Badge>
        )}
      </div>
      <CardHeader className="p-0 text-center">
        <CardTitle className="h-12 leading-5 text-base font-semibold overflow-hidden text-ellipsis line-clamp-2">{product.name}</CardTitle>
        {product.brand_name && <CardDescription className="text-sm text-muted-foreground">{product.brand_name}</CardDescription>}
      </CardHeader>
      <CardContent className="flex-grow px-3">
        <PriceDisplay prices={product.prices} />
      </CardContent>
      <CardFooter className="flex justify-center pb-0">
        <AddToCartButton product={product} />
      </CardFooter>
    </Card>
  );
};

export default ProductTile;