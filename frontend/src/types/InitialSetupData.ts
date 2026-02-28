import type { Cart } from './Cart';

export type InitialSetupData = {
  cart: Cart;
  anchor_map: { [storeId: number]: number };
  anonymous_id?: string;
};
