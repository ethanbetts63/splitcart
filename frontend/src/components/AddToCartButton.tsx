import React from 'react';
import { useCart } from '../context/CartContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import type { Product } from '../types';
import { useStoreList } from '../context/StoreListContext';
import { useDialog } from '../context/DialogContext';
import { toast } from "sonner";


interface AddToCartButtonProps {
  product: Product;
}

const AddToCartButton: React.FC<AddToCartButtonProps> = ({ product }) => {
  const { currentCart, addItem, updateItemQuantity } = useCart();
  const { selectedStoreIds } = useStoreList();
  const { openDialog } = useDialog();


  const items = currentCart?.items || [];
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = () => {
    if (selectedStoreIds.size === 0) {
      openDialog('Edit Location');
      toast.info("Please select your stores before adding to your cart.");
      return;
    }
    // No need to set loading state, the UI will update optimistically
    addItem(product.id, 1, product);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (existingItem) {
      updateItemQuantity(existingItem.id, newQuantity);
    }
  };

  if (existingItem) {
    return (
      <div className="flex items-center gap-2">
        <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange(existingItem.quantity - 1)}>-</Button>
        <Input
          type="number"
          readOnly
          className="h-8 w-12 text-center no-spinner"
          value={existingItem.quantity}
          min="1"
        />
        <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange(existingItem.quantity + 1)}>+</Button>
      </div>
    );
  }

  return (
    <Button onClick={handleAdd}>
      Add to Cart
    </Button>
  );
};

export default AddToCartButton;