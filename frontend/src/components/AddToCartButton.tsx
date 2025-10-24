import React, { useState } from 'react';
import { useCart } from '@/context/CartContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { Product } from '@/types';
import { Loader2 } from 'lucide-react';

interface AddToCartButtonProps {
  product: Product;
}

const AddToCartButton: React.FC<AddToCartButtonProps> = ({ product }) => {
  const { currentCart, addItem, updateItemQuantity } = useCart();
  const [isLoading, setIsLoading] = useState(false);

  const items = currentCart?.items || [];
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = async () => {
    setIsLoading(true);
    await addItem(product.id, 1);
    setIsLoading(false);
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
    <Button onClick={handleAdd} disabled={isLoading}>
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {isLoading ? 'Adding...' : 'Add to Cart'}
    </Button>
  );
};

export default AddToCartButton;