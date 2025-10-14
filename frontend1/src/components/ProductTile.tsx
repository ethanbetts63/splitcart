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
import '../css/ProductTile.css'; // Import the new CSS file
import { Product } from '@/types'; // Import shared type

interface ProductTileProps {
  product: Product;
}

const ProductTile: React.FC<ProductTileProps> = ({ product }) => {

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const imageUrl = product.image_url || fallbackImage;

  return (
    <Card className="product-tile-card">
      <div className="product-tile-image-container">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="product-tile-image"
        />
      </div>
      <CardHeader className="product-tile-header">
        <CardTitle className="product-tile-title">{product.name}</CardTitle>
        {product.brand_name && <CardDescription className="product-tile-description">{product.brand_name}</CardDescription>}
      </CardHeader>
      <CardContent className="product-tile-content">
        <PriceDisplay prices={product.prices} />
      </CardContent>
      <CardFooter className="product-tile-footer">
        <AddToCartButton product={product} />
      </CardFooter>
    </Card>
  );
};

export default ProductTile;