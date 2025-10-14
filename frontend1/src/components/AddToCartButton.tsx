import React from 'react';
import { useShoppingList } from '@/context/ShoppingListContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Define the types for props
type Product = {
  id: number;
  name: string;
  // Add other product properties as needed for the context
};

interface AddToCartButtonProps {
  product: Product;
}

const AddToCartButton: React.FC<AddToCartButtonProps> = ({ product }) => {
  const { items, addItem, updateItemQuantity, removeItem } = useShoppingList();
  const existingItem = items.find(item => item.product.id === product.id);

  const handleAdd = () => {
    addItem(product, 1);
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity > 0) {
      updateItemQuantity(product.id, newQuantity);
    } else {
      removeItem(product.id);
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
