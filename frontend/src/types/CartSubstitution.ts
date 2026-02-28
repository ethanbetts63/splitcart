import type { Product } from './Product';

export type CartSubstitution = {
  id: string;
  substituted_product: Product;
  quantity: number;
  is_approved: boolean;
  created_at?: string;
  updated_at?: string;
};
