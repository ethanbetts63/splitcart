import React from 'react';
import { useCart } from '../context/CartContext';
import { useStoreList } from '../context/StoreListContext';
import { useDialog } from '../context/DialogContext';
import { toast } from 'sonner';
import type { AddToCartButtonProps } from '../types/AddToCartButtonProps';

const AddToCartButton: React.FC<AddToCartButtonProps> = ({ product }) => {
  const { currentCart, addItem, updateItemQuantity } = useCart();
  const { selectedStoreIds } = useStoreList();
  const { openDialog } = useDialog();

  const items = currentCart?.items || [];
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = () => {
    if (selectedStoreIds.size === 0) {
      openDialog('Edit Location');
      toast.info('Please select your stores before adding to your cart.');
      return;
    }
    addItem(product.id, 1, product);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (existingItem) {
      updateItemQuantity(existingItem.id, newQuantity);
    }
  };

  if (existingItem) {
    return (
      <div className="flex items-center w-full rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
        <button
          onClick={() => handleQuantityChange(existingItem.quantity - 1)}
          className="flex-none w-9 h-9 flex items-center justify-center text-gray-600 hover:bg-gray-200 font-bold text-lg transition-colors duration-150"
          aria-label="Decrease quantity"
        >
          −
        </button>
        <span className="flex-grow text-center font-bold text-sm text-gray-900 select-none">
          {existingItem.quantity}
        </span>
        <button
          onClick={() => handleQuantityChange(existingItem.quantity + 1)}
          className="flex-none w-9 h-9 flex items-center justify-center bg-yellow-300 hover:bg-yellow-400 active:bg-yellow-500 font-bold text-black text-lg transition-colors duration-150"
          aria-label="Increase quantity"
        >
          +
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleAdd}
      className="w-full h-9 bg-yellow-300 hover:bg-yellow-400 active:bg-yellow-500 text-black font-bold text-sm rounded-lg transition-colors duration-150"
    >
      Add to Cart
    </button>
  );
};

export default AddToCartButton;
