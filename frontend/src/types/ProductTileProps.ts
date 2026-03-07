import type { Product } from './Product';

export interface ProductTileProps {
  product: Product;
  root?: Element | null;
  rootMargin?: string;
}
