import { Product } from './Product';

export interface CartSubstitution {
  id: string;
  substituted_product: Product;
  quantity: number;
  is_approved: boolean;
}