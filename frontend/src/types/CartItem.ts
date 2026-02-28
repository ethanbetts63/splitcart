import type { Product } from './Product';
import type { CartSubstitution } from './CartSubstitution';

export type CartItem = {
  id: string;
  product: Product;
  quantity: number;
  baseline_price?: number;
  substitutions?: CartSubstitution[];
  created_at?: string;
  updated_at?: string;
};
