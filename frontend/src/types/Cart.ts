import type { Product } from './Product';

export interface CartItem {
  id: string;
  product: Product;
  quantity: number;
}

export interface Cart {
  id: string;
  name: string;
  items: CartItem[];
  is_active: boolean;
}