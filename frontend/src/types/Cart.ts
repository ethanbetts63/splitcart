import type { CartItem } from './CartItem';

export interface Cart {
  id: string;
  name: string;
  items: CartItem[];
  is_active: boolean;
}