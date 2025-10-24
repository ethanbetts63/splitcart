import React, { useState, useEffect } from 'react';
import { useCart } from '@/context/CartContext';
import type { Cart } from '@/types';
import CartItemTile from '@/components/CartItemTile';
import NextButton from '@/components/NextButton';
import { useAuth } from '@/context/AuthContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PlusCircle, Save, Trash2, Pencil } from 'lucide-react';

interface cartPageProps {
  onOpenChange: (open: boolean) => void;
}

const CartPage: React.FC<cartPageProps> = ({ onOpenChange }) => {
  const { 
    currentCart, userCarts, cartLoading, 
    loadCart, createNewCart, renameCart, deleteCart 
  } = useCart();
  const { isAuthenticated } = useAuth();
  const [isEditingCartName, setIsEditingCartName] = useState(false);
  const [newCartName, setNewCartName] = useState(currentCart?.name || '');

  useEffect(() => {
    if (currentCart) {
      setNewCartName(currentCart.name);
    }
  }, [currentCart]);

  const cartTotal = currentCart?.items.reduce((total, item) => total + item.quantity, 0) || 0;

  const handleRenameCart = () => {
    if (currentCart && newCartName) {
      renameCart(currentCart.id, newCartName);
      setIsEditingCartName(false);
    }
  };

  const handleSwitchCart = (value: string) => {
    if (value === "new") {
      const newCartDefaultName = `Shopping List #${userCarts.length + 1}`;
      createNewCart(newCartDefaultName);
    } else if (value) {
      loadCart(value);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lg font-semibold">My Cart ({cartTotal} items)</h3>
        {currentCart && currentCart.items.length > 0 && (
          <NextButton onAfterNavigate={() => onOpenChange(false)} />
        )}
      </div>

      {isAuthenticated && (
        <div className="p-4 border-b flex flex-col gap-2">
            <div className="flex items-center gap-2">
                {isEditingCartName ? (
                    <Input
                        id="cart-name-edit"
                        type="text"
                        value={newCartName}
                        onChange={(e) => setNewCartName(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                handleRenameCart();
                                e.currentTarget.blur();
                            }
                        }}
                        disabled={cartLoading}
                        className="flex-grow"
                    />
                ) : (
                    <Select
                        value={currentCart?.id || ''}
                        onValueChange={handleSwitchCart}
                    >
                        <SelectTrigger className="flex-grow">
                            <SelectValue>
                                {currentCart?.name || 'Select a Cart'}
                            </SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="new">
                                <div className="flex items-center gap-2">
                                    <PlusCircle className="h-4 w-4" /> Create New Cart
                                </div>
                            </SelectItem>
                            {Array.isArray(userCarts) && userCarts.map((cart: Cart) => (
                                <SelectItem key={cart.id} value={cart.id}>
                                    {cart.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                )}
                <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => {
                        if (isEditingCartName) {
                            handleRenameCart();
                        } else {
                            setNewCartName(currentCart?.name || '');
                            setIsEditingCartName(true);
                        }
                    }}
                    disabled={cartLoading || !currentCart}
                    className={isEditingCartName ? "bg-green-500 text-white hover:bg-green-600" : ""}
                >
                    {isEditingCartName ? <Save className="h-4 w-4" /> : <Pencil className="h-4 w-4" />}
                </Button>
                <Button 
                    variant="destructive" 
                    size="icon"
                    onClick={() => currentCart && deleteCart(currentCart.id)}
                    disabled={cartLoading || !currentCart || isEditingCartName || userCarts.length <= 1}
                >
                    <Trash2 className="h-4 w-4" />
                </Button>
            </div>
        </div>
      )}

      <div className="flex-grow overflow-y-auto p-4">
        {cartLoading ? (
            <p>Loading cart...</p>
        ) : currentCart && currentCart.items.length > 0 ? (
          <div className="flex flex-col gap-4">
            {currentCart.items.map(item => (
              <CartItemTile key={item.id} product={item.product} context="cart" />
            ))}
          </div>
        ) : (
          <div className="text-center text-muted-foreground pt-8">
            <p>Your cart is empty.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CartPage;