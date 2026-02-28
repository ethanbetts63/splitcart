import type { Dispatch, SetStateAction } from 'react';
import type { Store } from './Store';
import type { MapBounds } from './MapBounds';

export interface StoreSearchContextType {
  stores: Store[] | null;
  setStores: Dispatch<SetStateAction<Store[] | null>>;
  postcode: string;
  setPostcode: Dispatch<SetStateAction<string>>;
  radius: number;
  setRadius: Dispatch<SetStateAction<number>>;
  selectedCompanies: string[];
  setSelectedCompanies: Dispatch<SetStateAction<string[]>>;
  mapBounds: MapBounds;
  setMapBounds: Dispatch<SetStateAction<MapBounds>>;
  isLoading: boolean;
  error: string | null;
  handleSearch: () => Promise<Store[] | null>;
}
