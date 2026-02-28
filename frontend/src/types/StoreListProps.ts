import type { Store } from './Store';

export interface StoreListProps {
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}
