import React from 'react';
import { Card } from "@/components/ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '@/assets/splitcart_symbol_v6.png';
import type { Product } from '@/types'; // Import shared type
import { useCart } from '@/context/CartContext';

import { Button } from '@/components/ui/button';

interface cartItemTileProps {
  product: Product;
  onApprove?: (product: Product) => void;
  isApproved?: boolean;
  quantity?: number;
  onQuantityChange?: (product: Product, quantity: number) => void;
  context?: 'cart' | 'substitution';
}

import { Badge } from "@/components/ui/badge";

import { Input } from '@/components/ui/input';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import CartSubTile from './CartSubTile';

// ... (rest of the imports)

const CartItemTile: React.FC<cartItemTileProps> = ({ product, onApprove, isApproved, quantity, onQuantityChange, context }) => {
  const { currentCart, updateItemQuantity, removeItem } = useCart();
  const items = currentCart?.items || [];

  const cartItem = context === 'cart' ? items.find(item => item.product.id === product.id) : null;
  const displayQuantity = context === 'cart' ? cartItem?.quantity : quantity;

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    e.currentTarget.src = fallbackImage;
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (context === 'cart' && cartItem) {
      if (newQuantity <= 0) {
        removeItem(cartItem.id);
      } else {
        updateItemQuantity(cartItem.id, newQuantity);
      }
    } else if (onQuantityChange) {
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

  const dummySubProduct: Product = {
    id: 999,
    name: "Dummy Sub Product",
    brand_name: "Dummy Brand",
    size: "1kg",
    image_url: "https://via.placeholder.com/150",
    prices: [],
  };

  return (
    <Card className="p-2">
      <div className="flex flex-row items-center gap-0 relative">
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
          {context === 'cart' && cartItem ? (
            <div className="flex items-center gap-2">
              <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange((displayQuantity || 1) - 1)}>-</Button>
              <Input
                type="number"
                readOnly
                className="h-8 w-12 text-center no-spinner"
                value={displayQuantity}
                min="0"
              />
              <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange((displayQuantity || 1) + 1)}>+</Button>
            </div>
          ) : onApprove ? (
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
      </div>
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="item-1">
          <AccordionTrigger className="w-full flex justify-center p-2 text-sm text-muted-foreground">
            Show Substitutions (3)
          </AccordionTrigger>
          <AccordionContent>
            <CartSubTile product={dummySubProduct} quantity={1} />
            <CartSubTile product={dummySubProduct} quantity={2} />
            <CartSubTile product={dummySubProduct} quantity={1} />
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );
};

export default CartItemTile;