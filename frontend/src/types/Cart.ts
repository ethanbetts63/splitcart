import type { CartItem } from './CartItem';

export type Cart = {
  id: string;
  name: string;
  items: CartItem[];
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};
