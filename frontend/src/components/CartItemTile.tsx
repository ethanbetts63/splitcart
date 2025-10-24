import React from 'react';
import { Card } from "@/components/ui/card";
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '@/assets/splitcart_symbol_v6.png';
import type { Product, CartSubstitution } from '@/types'; // Import shared type
import { useCart } from '@/context/CartContext';

import { Button } from '@/components/ui/button';

// New type for callbacks
type OnApproveCallback = (sub: CartSubstitution) => Promise<void>;
type OnQuantityChangeCallback = (sub: CartSubstitution, quantity: number) => Promise<void>;

interface BaseCartItemTileProps {
  context?: 'cart' | 'substitution';
}

interface CartContextProps extends BaseCartItemTileProps {
  context: 'cart';
  product: Product; // For displaying original cart items
}

interface SubstitutionContextProps extends BaseCartItemTileProps {
  context: 'substitution';
  cartSubstitution: CartSubstitution; // For displaying substitute items
  onApprove: OnApproveCallback; // Mandatory for substitution context
  onQuantityChange: OnQuantityChangeCallback; // Mandatory for substitution context
}

// Combine into a single type using a discriminated union
type CartItemTileProps = CartContextProps | SubstitutionContextProps;

import { Badge } from "@/components/ui/badge";

import { Input } from '@/components/ui/input';

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import CartSubTile from './CartSubTile';

// ... (rest of the imports)

const CartItemTile: React.FC<CartItemTileProps> = (props) => {
  const { context } = props;

  // Conditionally assign variables based on context
  const product = context === 'cart' ? props.product : props.cartSubstitution.substituted_product;
  const cartSubstitution = context === 'substitution' ? props.cartSubstitution : undefined;
  const onApprove = context === 'substitution' ? props.onApprove : undefined;
  const onQuantityChange = context === 'substitution' ? props.onQuantityChange : undefined;

  // For 'substitution' context, quantity and isApproved come from cartSubstitution
  const displayQuantity = cartSubstitution ? cartSubstitution.quantity : (context === 'cart' ? (props as CartContextProps).product.quantity : 0); // This will need careful handling
  const isApproved = cartSubstitution ? cartSubstitution.is_approved : false;

  const { currentCart, updateItemQuantity, removeItem } = useCart();
  const items = currentCart?.items || [];

  const cartItem = context === 'cart' ? items.find(item => item.product.id === product.id) : null;

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
    } else if (context === 'substitution' && cartSubstitution && onQuantityChange) {
      // The logic for quantity <= 0 and setting is_approved=false is handled by SubstitutionPage.tsx
      // CartItemTile just needs to pass the new quantity and the cartSubstitution object
      onQuantityChange(cartSubstitution, newQuantity);
    }
  };

  const imageUrl = product.image_url || fallbackImage;

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
          ) : (context === 'substitution' && cartSubstitution) ? (
            isApproved ? (
              <div className="flex items-center gap-2">
                <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange(cartSubstitution.quantity - 1)}>-</Button>
                <Input
                  type="number"
                  readOnly
                  className="h-8 w-12 text-center no-spinner"
                  value={cartSubstitution.quantity}
                  min="0"
                />
                <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange(cartSubstitution.quantity + 1)}>+</Button>
              </div>
            ) : (
              <Button onClick={() => onApprove && onApprove(cartSubstitution)} className="bg-green-500 hover:bg-green-600">
                Approve
              </Button>
            )
          ) : (
            <AddToCartButton product={product} />
          )}
        </div>
      </div>
      {/* Accordion for Substitutions (will be populated later) */}
      <Accordion type="single" collapsible className="w-full">
        <AccordionItem value="item-1">
          <AccordionTrigger className="w-full flex justify-center p-2 text-sm text-muted-foreground">
            Show Substitutions
          </AccordionTrigger>
          <AccordionContent>
            {/* CartSubTile components will be rendered here based on actual data */}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </Card>
  );
};

export default CartItemTile;