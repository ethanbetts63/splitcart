import type { Product } from '@/types/Product';

type CartItem = {
  product: Product;
  quantity: number;
};

export { type CartItem };
