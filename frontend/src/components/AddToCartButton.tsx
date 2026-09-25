'use client';

import { useCart } from '../context/CartContext';
import type { AddToCartButtonProps } from '../types/AddToCartButtonProps';

const AddToCartButton = ({ product }: AddToCartButtonProps) => {
  const { currentCart, addItem, updateItemQuantity } = useCart();

  const items = currentCart?.items || [];
  const existingItem = items.find((item) => item.product.id === product.id);

  const handleQuantityChange = (newQuantity: number) => {
    if (existingItem) {
      updateItemQuantity(existingItem.id, newQuantity);
    }
  };

  if (existingItem) {
    return (
      <div className="flex items-center w-full rounded-lg overflow-hidden border border-border-default bg-surface-sunken">
        <button
          onClick={() => handleQuantityChange(existingItem.quantity - 1)}
          className="flex-none w-9 h-9 flex items-center justify-center text-text-secondary hover:bg-surface-sunken-strong font-bold text-lead transition-colors duration-150"
          aria-label="Decrease quantity"
        >
          −
        </button>
        <span className="flex-grow text-center font-bold text-body text-text-primary select-none">
          {existingItem.quantity}
        </span>
        <button
          onClick={() => handleQuantityChange(existingItem.quantity + 1)}
          className="flex-none w-9 h-9 flex items-center justify-center bg-action-primary hover:bg-action-primary-hover active:bg-action-primary-active font-bold text-text-on-brand text-lead transition-colors duration-150"
          aria-label="Increase quantity"
        >
          +
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => addItem(product.id, 1, product)}
      className="w-full h-9 bg-action-primary hover:bg-action-primary-hover active:bg-action-primary-active text-text-on-brand font-bold text-body rounded-lg transition-colors duration-150"
    >
      Add to Cart
    </button>
  );
};

export default AddToCartButton;
