import type { Store } from './Store';
import type { AnchorMap } from './AnchorMap';

export interface NearbyStoresResponse {
  stores: Store[];
  anchor_map: AnchorMap;
}
