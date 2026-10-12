import { useQuery, type QueryKey } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import type { ApiOptions } from '../types/ApiOptions';
import { getApiUrl } from '@/lib/apiUrl';
import { authedFetch } from '@/services/apiClient';

const apiFetch = async <T>(
  endpoint: string,
  anonymousId: string | null,
  options: ApiOptions = {},
): Promise<T> => {
  const { method = 'GET', body, ...restOptions } = options;

  const headers: Record<string, string> = {
    ...(restOptions.headers as Record<string, string>),
  };
  if (anonymousId) headers['X-Anonymous-ID'] = anonymousId;

  const response = await authedFetch(getApiUrl(endpoint), {
    ...restOptions,
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData: unknown = await response.json();
      if (typeof errorData === 'object' && errorData !== null) {
        const { detail, error } = errorData as { detail?: string; error?: string };
        errorMessage = detail ?? error ?? errorMessage;
      }
    } catch {
      // Response was not JSON, stick with the status text
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
};

export const useApiQuery = <T>(
  queryKey: QueryKey,
  endpoint: string,
  options: Omit<ApiOptions, 'body' | 'method'> = {},
  reactQueryOptions: {
    enabled?: boolean;
    refetchOnWindowFocus?: boolean;
    staleTime?: number;
  } = {},
) => {
  const { anonymousId } = useAuth();

  return useQuery<T, Error>({
    queryKey,
    queryFn: () => apiFetch<T>(endpoint, anonymousId, { ...options, method: 'GET' }),
    ...reactQueryOptions,
  });
};
