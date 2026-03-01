import type { Cart } from './Cart';
import type { ApiResponse } from './ApiResponse';

export interface CartContextType {
  currentCart: Cart | null;
  userCarts: Cart[];
  optimizationResult: ApiResponse | null;
  setOptimizationResult: (result: ApiResponse | null) => void;
  cartLoading: boolean;
  isCartSyncing: boolean;
  fetchActiveCart: () => Promise<Cart | null>;
  loadCart: (cartId: string) => void;
  createNewCart: () => void;
  renameCart: (cartId: string, newName: string) => void;
  deleteCart: (cartId: string) => void;
  addItem: (productId: number, quantity: number, product: any) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  optimizeCurrentCart: () => Promise<ApiResponse | null>;
  emailCurrentCart: (exportData: any) => Promise<void>;
  downloadCurrentCart: (exportData: any) => Promise<Blob | null>;
  updateCartItemSubstitution: (cartItemId: string, substitutionId: string, isApproved: boolean, quantity: number) => void;
}
