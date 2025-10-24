import type { Product } from '@/types/Product';
import type { CartSubstitution } from '@/types/CartSubstitution';

type CartItem = {
  id: string; // Assuming CartItem has an ID
  product: Product;
  quantity: number;
  substitutions?: CartSubstitution[]; // Add substitutions array
};

export { type CartItem };
