import React from 'react';
import { useCart } from '@/context/CartContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { Product } from '@/types/Product'; // Import shared type

// import { useSubstitutions } from '@/context/SubstitutionContext';
// import { useStoreList } from '@/context/StoreListContext';

interface AddToCartButtonProps {
  product: Product;
}

const AddToCartButton: React.FC<AddToCartButtonProps> = ({ product }) => {
  const { items, addItem, updateItemQuantity } = useCart();
  // const { fetchSubstitutes } = useSubstitutions();
  // const { selectedStoreIds } = useStoreList();
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = () => {
    addItem(product, 1);
    // fetchSubstitutes(product, Array.from(selectedStoreIds));
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (existingItem) {
      updateItemQuantity(existingItem.id, newQuantity);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuantity = parseInt(e.target.value, 10);
    if (!isNaN(newQuantity) && newQuantity > 0) {
        handleQuantityChange(newQuantity);
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
          onChange={handleInputChange}
          min="1"
        />
        <Button size="icon" className="h-8 w-8" onClick={() => handleQuantityChange(existingItem.quantity + 1)}>+</Button>
      </div>
    );
  }

  return (
    <Button onClick={handleAdd}>Add to Cart</Button>
  );
};

export default AddToCartButton;