import { type ApiClient } from './apiClient';
import { type AnchorMap } from '../context/StoreListContext';

type ApiStore = {
  id: number;
  store_name: string;
  company_name: string;
  latitude: number;
  longitude: number;
};

export interface NearbyStoresResponse {
    stores: ApiStore[];
    anchor_map: AnchorMap;
}

interface SearchParams {
    postcode: string;
    radius: number;
    companies: string[];
}

export const searchNearbyStoresAPI = (apiClient: ApiClient, { postcode, radius, companies }: SearchParams): Promise<NearbyStoresResponse> => {
    const params = new URLSearchParams();
    params.append('postcode', postcode);
    params.append('radius', radius.toString());
    if (companies.length > 0) {
      params.append('companies', companies.join(','));
    }
    
    return apiClient.get<NearbyStoresResponse>(`/api/stores/nearby/?${params.toString()}`);
};
