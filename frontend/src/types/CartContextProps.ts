import type { BaseCartItemTileProps } from './BaseCartItemTileProps';
import type { Product } from './Product';

export interface CartContextProps extends BaseCartItemTileProps {
  context: 'cart';
  product: Product;
}
