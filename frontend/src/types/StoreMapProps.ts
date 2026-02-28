import type { Store } from './Store';
import type { MapBounds } from './MapBounds';

export interface StoreMapProps {
  bounds: MapBounds;
  stores: Store[];
  selectedStoreIds: Set<number>;
  onStoreSelect: (storeId: number) => void;
}
