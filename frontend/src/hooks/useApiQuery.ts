
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import type { ApiOptions } from '../types/ApiOptions';

// --- Centralized API Fetch Function ---

const apiFetch = async <T>(
  endpoint: string,
  token: string | null,
  anonymousId: string | null,
  options: ApiOptions = {}
): Promise<T> => {
  const { method = 'GET', body, ...restOptions } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(restOptions.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Token ${token}`;
  } else if (anonymousId) {
    headers['X-Anonymous-ID'] = anonymousId;
  }

  const config: RequestInit = {
    method,
    headers,
    ...restOptions,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  // Prepend /api if it's not already there
  const finalEndpoint = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`;

  const response = await fetch(finalEndpoint, config);

  if (!response.ok) {
    if (response.status === 401) {
      // Dispatch a custom event to be caught by the AuthProvider
      window.dispatchEvent(new CustomEvent('unauthorized'));
    }
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.error || errorMessage;
    } catch (e) {
      // Response was not JSON, stick with the status text
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
};

// --- Custom Hook for Queries (GET requests) ---

export const useApiQuery = <T>(
  queryKey: any[],
  endpoint: string,
  options: Omit<ApiOptions, 'body' | 'method'> = {},
  reactQueryOptions: {
    enabled?: boolean;
    refetchOnWindowFocus?: boolean;
    staleTime?: number;
  } = {}
) => {
  const { token, anonymousId } = useAuth();

  return useQuery<T, Error>({
    queryKey,
    queryFn: () => apiFetch<T>(endpoint, token, anonymousId, { ...options, method: 'GET' }),
    ...reactQueryOptions,
  });
};

// --- Custom Hook for Mutations (POST, PUT, PATCH, DELETE) ---

export const useApiMutation = <T, U>(
  // Endpoint can be a function of variables
  endpoint: string | ((variables: U) => string),
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE'
) => {
  const { token, anonymousId } = useAuth();

  return useMutation<T, Error, U>({
    mutationFn: (variables: U) => {
      const finalEndpoint = typeof endpoint === 'function' ? endpoint(variables) : endpoint;
      return apiFetch<T>(finalEndpoint, token, anonymousId, { method, body: variables });
    },
  });
};
