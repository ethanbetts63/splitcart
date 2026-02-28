import { type ApiClient } from './apiClient';
import type { NearbyStoresResponse } from '../types/NearbyStoresResponse';
import type { SearchParams } from '../types/SearchParams';

export const searchNearbyStoresAPI = (apiClient: ApiClient, { postcode, radius, companies }: SearchParams): Promise<NearbyStoresResponse> => {
    const params = new URLSearchParams();
    params.append('postcode', postcode);
    params.append('radius', radius.toString());
    if (companies.length > 0) {
      params.append('companies', companies.join(','));
    }
    
    return apiClient.get<NearbyStoresResponse>(`/api/stores/nearby/?${params.toString()}`);
};
