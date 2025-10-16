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
  quantity?: number;
  onQuantityChange?: (product: Product, quantity: number) => void;
  context?: 'trolley' | 'substitution';
}

import { Badge } from "@/components/ui/badge";

import { Input } from '@/components/ui/input';

const TrolleyItemTile: React.FC<TrolleyItemTileProps> = ({ product, onApprove, isApproved, quantity, onQuantityChange, context }) => {

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const getShortDescription = (description?: string) => {
    if (!description) return '';
    if (description.includes('different size')) return 'Different Size';
    if (description.includes('similar product')) return 'Similar Product';
    if (description.includes('Same category')) return 'Similar Category';
    if (description.includes('Linked category')) return 'Related Category';
    return description;
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (onQuantityChange) {
      if (newQuantity <= 0) {
        if (onApprove) {
          onApprove(product);
        }
      } else {
        onQuantityChange(product, newQuantity);
      }
    }
  };

  const imageUrl = product.image_url || fallbackImage;

  return (
    <Card className="p-2 flex flex-row items-center gap-0 relative">
      {product.level_description && (
        <Badge variant="secondary" className="absolute top-2 right-2 z-10 bg-blue-500 text-white dark:bg-blue-600">{getShortDescription(product.level_description)}</Badge>
      )}
      {/* Image */}
      <div className="w-28 h-28 flex-shrink-0">
        <img
          src={imageUrl}
          onError={handleImageError}
          alt={product.name}
          className="h-full w-full object-cover rounded-md"
        />
      </div>

      {/* Middle Section: Info & Price */}
      <div className="flex-grow grid gap-1 justify-items-center">
        <div className="flex justify-center">
          <p className={`font-semibold text-center ${context === 'substitution' ? 'line-clamp-1' : ''}`}>{product.name}</p>
        </div>
        {product.size && <Badge variant="default">{product.size}</Badge>}
        <PriceDisplay prices={product.prices} />
      </div>

      {/* Right Section: Quantity Controls */}
      <div className="flex-shrink-0">
        {onApprove ? (
          isApproved ? (
            <div className="flex items-center gap-2">
              <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange((quantity || 1) - 1)}>-</Button>
              <Input
                type="number"
                readOnly
                className="h-8 w-12 text-center no-spinner"
                value={quantity}
                min="0"
              />
              <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange((quantity || 1) + 1)}>+</Button>
            </div>
          ) : (
            <Button onClick={() => onApprove && onApprove(product)} className="bg-green-500 hover:bg-green-600">
              Approve
            </Button>
          )
        ) : (
          <AddToCartButton product={product} />
        )}
      </div>
    </Card>
  );
};

export default TrolleyItemTile;