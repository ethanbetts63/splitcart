'use client';

import type { SyntheticEvent } from 'react';
import AddToCartButton from './AddToCartButton';
import PriceDisplay from './PriceDisplay';
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import { useCart } from '../context/CartContext';
import { Badge } from './ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import CartSubTile from './CartSubTile';
import { CheckCircle2 } from 'lucide-react';
import type { CartItemTileProps } from '../types/CartItemTileProps';
import { assetSrc } from '@/lib/assets';
import { cn } from '@/lib/utils';

const QuantityStepper = ({
  value,
  onDecrement,
  onIncrement,
}: {
  value: number;
  onDecrement: () => void;
  onIncrement: () => void;
}) => (
  <div className="flex items-center rounded-lg overflow-hidden border border-border-default bg-surface-sunken">
    <button
      onClick={onDecrement}
      className="w-8 h-8 flex items-center justify-center text-text-secondary hover:bg-surface-sunken-strong font-bold text-body transition-colors"
      aria-label="Decrease quantity"
    >
      −
    </button>
    <span className="w-8 text-center font-bold text-body text-text-primary select-none">
      {value}
    </span>
    <button
      onClick={onIncrement}
      className="w-8 h-8 flex items-center justify-center bg-action-primary hover:bg-action-primary-hover font-bold text-text-on-brand text-body transition-colors"
      aria-label="Increase quantity"
    >
      +
    </button>
  </div>
);

const CartItemTile = (props: CartItemTileProps) => {
  const { context, hideApprovedSubstitutions } = props;

  const product = context === 'cart' ? props.product : props.cartSubstitution.substituted_product;
  const cartSubstitution = context === 'substitution' ? props.cartSubstitution : undefined;
  const onApprove = context === 'substitution' ? props.onApprove : undefined;
  const onQuantityChange = context === 'substitution' ? props.onQuantityChange : undefined;

  const { currentCart, updateItemQuantity, removeItem } = useCart();
  const items = currentCart?.items || [];
  const cartItem = context === 'cart' ? items.find((item) => item.product.id === product.id) : null;

  if (context === 'cart' && !cartItem) return null;

  const displayQuantity = cartSubstitution
    ? cartSubstitution.quantity
    : cartItem
      ? cartItem.quantity
      : 0;
  const isApproved = cartSubstitution ? cartSubstitution.is_approved : false;

  const handleImageError = (e: SyntheticEvent<HTMLImageElement, Event>) => {
    if (e.currentTarget.src !== assetSrc(fallbackImage))
      e.currentTarget.src = assetSrc(fallbackImage);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (context === 'cart' && cartItem) {
      if (newQuantity <= 0) removeItem(cartItem.id);
      else updateItemQuantity(cartItem.id, newQuantity);
    } else if (context === 'substitution' && cartSubstitution && onQuantityChange) {
      onQuantityChange(cartSubstitution, newQuantity);
    }
  };

  const imageUrl = product.image_url || assetSrc(fallbackImage);

  return (
    <div
      className={cn(
        'rounded-xl border bg-surface-page shadow-sm overflow-hidden',
        isApproved ? 'border-border-success' : 'border-border-default',
      )}
    >
      <div className="flex items-center gap-3 p-3">
        {/* Image */}
        <div className="flex-shrink-0 w-16 h-16">
          <img
            src={imageUrl}
            onError={handleImageError}
            alt={product.name}
            className="w-full h-full object-cover rounded-lg border border-border-subtle"
          />
        </div>

        {/* Info */}
        <div className="flex-grow min-w-0">
          <p
            className={cn(
              'font-semibold text-text-primary text-body leading-snug',
              context === 'substitution' ? 'line-clamp-2' : 'line-clamp-1',
            )}
          >
            {product.name}
          </p>
          {product.size && (
            <Badge variant="outline" className="px-1.5 py-0 mt-0.5">
              {product.size}
            </Badge>
          )}
          <div className="mt-1">
            <PriceDisplay prices={product.prices} />
          </div>
        </div>

        {/* Action */}
        <div className="flex-shrink-0">
          {context === 'cart' && cartItem ? (
            <QuantityStepper
              value={displayQuantity || 1}
              onDecrement={() => handleQuantityChange((displayQuantity || 1) - 1)}
              onIncrement={() => handleQuantityChange((displayQuantity || 1) + 1)}
            />
          ) : context === 'substitution' && cartSubstitution ? (
            isApproved ? (
              <QuantityStepper
                value={cartSubstitution.quantity}
                onDecrement={() => handleQuantityChange(cartSubstitution.quantity - 1)}
                onIncrement={() => handleQuantityChange(cartSubstitution.quantity + 1)}
              />
            ) : (
              <button
                onClick={() => onApprove && onApprove(cartSubstitution)}
                className="px-3 py-1.5 text-body font-bold bg-action-primary hover:bg-action-primary-hover active:bg-action-primary-active text-text-on-brand rounded-lg transition-colors duration-150"
              >
                Approve
              </button>
            )
          ) : (
            <AddToCartButton product={product} />
          )}
        </div>
      </div>

      {/* Approved indicator strip */}
      {context === 'substitution' && isApproved && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-surface-success border-t border-border-success">
          <CheckCircle2 className="h-3.5 w-3.5 text-fill-success flex-shrink-0" />
          <span className="text-label font-semibold text-text-success">Approved as substitute</span>
        </div>
      )}

      {/* Cart context: approved substitutions accordion */}
      {context === 'cart' &&
        !hideApprovedSubstitutions &&
        cartItem &&
        cartItem.substitutions &&
        cartItem.substitutions.filter((sub) => sub.is_approved).length > 0 && (
          <Accordion type="single" collapsible className="w-full border-t border-border-subtle">
            <AccordionItem value="item-1" className="border-0">
              <AccordionTrigger className="w-full flex justify-center px-3 py-2 text-body text-text-subtle hover:text-text-secondary">
                Show {cartItem.substitutions.filter((sub) => sub.is_approved).length} Approved
                Substitution(s)
              </AccordionTrigger>
              <AccordionContent className="pb-0">
                {cartItem.substitutions
                  .filter((sub) => sub.is_approved)
                  .map((sub) => (
                    <CartSubTile key={sub.id} cartSubstitution={sub} cartItemId={cartItem.id} />
                  ))}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        )}
    </div>
  );
};

export default CartItemTile;
