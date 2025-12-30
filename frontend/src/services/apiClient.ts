import { getAuthHeaders } from '../lib/utils';

export class ApiError extends Error {
  statusCode: number;
  data: any;

  constructor(statusCode: number, message: string, data: any = null) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

interface ApiClientOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: Record<string, any> | FormData;
  signal?: AbortSignal;
}

export class ApiClient {
  private token: string | null;
  private anonymousId: string | null;

  constructor(token: string | null, anonymousId: string | null) {
    this.token = token;
    this.anonymousId = anonymousId;
  }

  private async request<T>(url: string, options: ApiClientOptions = {}): Promise<T> {
    const headers = getAuthHeaders(this.token, this.anonymousId);
    
    const config: RequestInit = {
      method: options.method || 'GET',
      headers: headers,
      signal: options.signal,
    };

    if (options.body) {
      if (options.body instanceof FormData) {
        // FormData doesn't need Content-Type header set explicitly,
        // browser sets it with boundary.
        delete (config.headers as Record<string, string>)['Content-Type'];
        config.body = options.body;
      } else {
        config.body = JSON.stringify(options.body);
      }
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      let errorData: any = null;
      try {
        errorData = await response.json();
      } catch (e) {
        // If response is not JSON, use status text
        errorData = { message: response.statusText || 'Unknown error' };
      }
      throw new ApiError(
        response.status,
        errorData.detail || errorData.error || errorData.message || `API request failed with status ${response.status}`,
        errorData
      );
    }

    // Handle cases where response might be empty (e.g., DELETE requests)
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json() as Promise<T>;
    }
    return Promise.resolve() as Promise<T>; // Resolve with undefined for non-JSON responses
  }

  get<T>(url: string, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'GET', signal });
  }

  post<T>(url: string, body: Record<string, any> | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'POST', body, signal });
  }

  put<T>(url: string, body: Record<string, any> | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'PUT', body, signal });
  }

  patch<T>(url: string, body: Record<string, any> | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'PATCH', body, signal });
  }

  delete<T>(url: string, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'DELETE', signal });
  }
}

// Helper to create an API client instance
export const createApiClient = (token: string | null, anonymousId: string | null): ApiClient => {
    return new ApiClient(token, anonymousId);
};
