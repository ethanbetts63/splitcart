import React, { useActionState, useState } from 'react';
import { z } from 'zod';
import { useCart } from '../../context/CartContext';
import type { Cart } from '../../types';
import CartItemTile from '../../components/CartItemTile';
import NextButton from '../../components/NextButton';
import { useAuth } from '../../context/AuthContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { PlusCircle, Save, Trash2, Pencil } from 'lucide-react';
import { FIELD_MAX } from '@/lib/fieldMax';
import type { CartPageProps } from '../../types/CartPageProps';
import { cartRenameSchema } from './CartPage.schema';

/**
 * The rename control is a real `<form>` (FORMS-1), Track B: one field, one
 * submit, `useActionState` over an action that parses `FormData` against
 * `CartPage.schema.ts`. It used to be a bare `<Input>` whose only route to the
 * network was an `onKeyDown` watching for Enter; form semantics give that back
 * for free, and give the field a schema it never had.
 *
 * Not a Server Action: `renameCart` reaches Django through `apiClient`, which
 * attaches a DRF token held in `localStorage` by client JavaScript. There is no
 * session for a Next server to forward, which is why FORMS-9/10/11 are `n/a`
 * here -- see `_docs/convergence/auth-migration.md`.
 */
interface RenameState {
  /** A schema failure. A *network* failure is already a toast from `renameCart`. */
  error?: string;
  /** Bumped on each accepted submit, so the editor knows to close. */
  submitted?: number;
}

const CartPage: React.FC<CartPageProps> = ({ onOpenChange }) => {
  const { currentCart, userCarts, cartLoading, loadCart, createNewCart, renameCart, deleteCart } =
    useCart();
  const { isAuthenticated } = useAuth();
  const [isEditingCartName, setIsEditingCartName] = useState(false);
  const [newCartName, setNewCartName] = useState(currentCart?.name || '');

  // The rename field follows the active cart. Adjusted during render rather
  // than in an effect so the field never paints the previous cart's name and
  // then swap - see React's "adjusting state when a prop changes".
  const [lastCart, setLastCart] = useState<Cart | null>(currentCart);
  if (lastCart !== currentCart) {
    setLastCart(currentCart);
    if (currentCart) setNewCartName(currentCart.name);
  }

  const cartTotal = currentCart?.items.length || 0;

  const [renameState, renameAction] = useActionState(
    async (previous: RenameState, formData: FormData): Promise<RenameState> => {
      const parsed = cartRenameSchema.safeParse({ new_name: formData.get('new_name') });
      if (!parsed.success) {
        return { error: z.flattenError(parsed.error).fieldErrors.new_name?.[0] };
      }
      if (!currentCart) return { error: 'There is no cart to rename.' };
      // `renameCart` reports its own failures as a toast and resolves either
      // way, so there is nothing here to distinguish; the editor closes and the
      // list shows whichever name the server kept.
      await renameCart(currentCart.id, parsed.data.new_name);
      return { submitted: (previous.submitted ?? 0) + 1 };
    },
    {},
  );

  // The editor closes when a submit is accepted. Adjusted during render rather
  // than in an effect, the same way the field above follows the active cart: an
  // effect that calls setState is a second render pass for something already
  // known while the first one is running.
  const [lastSubmitted, setLastSubmitted] = useState(renameState.submitted);
  if (lastSubmitted !== renameState.submitted) {
    setLastSubmitted(renameState.submitted);
    setIsEditingCartName(false);
  }

  const handleSwitchCart = (value: string) => {
    if (value === 'new') {
      createNewCart();
    } else if (value) {
      loadCart(value);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <h3 className="text-lead font-semibold">My Cart ({cartTotal} items)</h3>
        {currentCart && currentCart.items.length > 0 && (
          <NextButton onAfterNavigate={() => onOpenChange(false)} />
        )}
      </div>

      {isAuthenticated && (
        <div className="p-4 border-b flex flex-col gap-2">
          <div className="flex items-center gap-2">
            {isEditingCartName ? (
              <form action={renameAction} className="flex flex-grow items-center gap-2">
                <Input
                  id="cart-name-edit"
                  name="new_name"
                  type="text"
                  required
                  maxLength={FIELD_MAX.line}
                  value={newCartName}
                  onChange={(e) => setNewCartName(e.target.value)}
                  disabled={cartLoading}
                  aria-invalid={renameState.error ? true : undefined}
                  className="flex-grow"
                />
                <Button
                  type="submit"
                  variant="outline"
                  size="icon"
                  disabled={cartLoading || !currentCart}
                  className="bg-fill-success text-text-on-dark hover:bg-fill-success"
                >
                  <Save className="h-4 w-4" />
                </Button>
              </form>
            ) : (
              <>
                <Select value={currentCart?.id || ''} onValueChange={handleSwitchCart}>
                  <SelectTrigger className="flex-grow">
                    <SelectValue>{currentCart?.name || 'Select a Cart'}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new">
                      <div className="flex items-center gap-2">
                        <PlusCircle className="h-4 w-4" /> Create New Cart
                      </div>
                    </SelectItem>
                    {Array.isArray(userCarts) &&
                      userCarts.map((cart: Cart) => (
                        <SelectItem key={cart.id} value={cart.id}>
                          {cart.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setNewCartName(currentCart?.name || '');
                    setIsEditingCartName(true);
                  }}
                  disabled={cartLoading || !currentCart}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
              </>
            )}
            <Button
              variant="destructive"
              size="icon"
              onClick={() => currentCart && deleteCart(currentCart.id)}
              disabled={cartLoading || !currentCart || isEditingCartName || userCarts.length <= 1}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
          {isEditingCartName && renameState.error && (
            <p className="text-caption text-text-danger">{renameState.error}</p>
          )}
        </div>
      )}

      <div className="flex-grow overflow-y-auto p-4">
        {cartLoading ? (
          <p>Loading cart...</p>
        ) : currentCart && currentCart.items.length > 0 ? (
          <div className="flex flex-col gap-4">
            {currentCart.items.map((item) => (
              <CartItemTile key={item.id} product={item.product} context="cart" />
            ))}
          </div>
        ) : (
          <div className="text-center text-text-muted pt-8">
            <p>Your cart is empty.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CartPage;
