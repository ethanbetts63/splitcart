import React from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from "./ui/badge";
import fallbackImage from '../assets/splitcart_symbol_v6.webp';
import type { CartSubstitution } from '../types';
import { useCart } from '../context/CartContext';

interface CartSubTileProps {
  cartSubstitution: CartSubstitution;
  cartItemId: string;
}

const CartSubTile: React.FC<CartSubTileProps> = ({ cartSubstitution, cartItemId }) => {
  const { substituted_product: product, quantity } = cartSubstitution;
  const { updateCartItemSubstitution } = useCart();

  if (!product) {
    return null; // Don't render if there is no product data
  }

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    if (e.currentTarget.src !== fallbackImage) {
      e.currentTarget.src = fallbackImage;
    }
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 1) {
      // This is the "disapprove" action. Keep the quantity, but set is_approved to false.
      updateCartItemSubstitution(cartItemId, cartSubstitution.id, false, cartSubstitution.quantity);
    } else {
      // This is a normal quantity update, ensure it remains approved.
      updateCartItemSubstitution(cartItemId, cartSubstitution.id, true, newQuantity);
    }
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
        <Button size="icon" className="h-6 w-6" onClick={() => handleQuantityChange(quantity - 1)}>-</Button>
        <Input
          type="number"
          readOnly
          className="h-6 w-10 text-center no-spinner"
          value={quantity}
          min="0"
        />
        <Button size="icon" className="h-6 w-6" onClick={() => handleQuantityChange(quantity + 1)}>+</Button>
      </div>
    </div>
  );
};

export default CartSubTile;
