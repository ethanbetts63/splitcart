import type { CartItem } from './CartItem';
import type { SelectedStoreListType } from './SelectedStoreListType';

export type Cart = {
  id: string;
  name: string;
  items: CartItem[];
  is_active: boolean;
  selected_store_list?: SelectedStoreListType;
  created_at?: string;
  updated_at?: string;
};
