import type { BaseCartItemTileProps } from './BaseCartItemTileProps';
import type { CartSubstitution } from './CartSubstitution';
import type { OnApproveCallback } from './OnApproveCallback';
import type { OnQuantityChangeCallback } from './OnQuantityChangeCallback';

export interface SubstitutionContextProps extends BaseCartItemTileProps {
  context: 'substitution';
  cartSubstitution: CartSubstitution;
  onApprove: OnApproveCallback;
  onQuantityChange: OnQuantityChangeCallback;
}
