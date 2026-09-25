import { getAuthHeaders } from '../lib/authHeaders';
import type { ApiClientOptions } from '../types/ApiClientOptions';
import type { ApiErrorBody } from '../types/ApiErrorBody';
import type { JsonBody } from '../types/JsonBody';
import { getApiUrl } from '@/lib/apiUrl';

export class ApiError extends Error {
  statusCode: number;
  data: ApiErrorBody | null;

  constructor(statusCode: number, message: string, data: ApiErrorBody | null = null) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Read the body of an unsuccessful response without trusting it.
 *
 * `Response.json()` is typed `any`, so the parse is widened to `unknown` and
 * narrowed by an actual runtime check: an error page, an empty body or a
 * proxy's HTML all reach here, and only an object has the fields the caller
 * goes on to read.
 */
const readErrorBody = async (response: Response): Promise<ApiErrorBody> => {
  try {
    const parsed: unknown = await response.json();
    if (typeof parsed === 'object' && parsed !== null) {
      return parsed as ApiErrorBody;
    }
    return { message: response.statusText || 'Unknown error' };
  } catch {
    // Not JSON at all - fall back to the status line.
    return { message: response.statusText || 'Unknown error' };
  }
};

const errorMessage = (body: ApiErrorBody, status: number): string =>
  body.detail ?? body.error ?? body.message ?? `API request failed with status ${status}`;

/**
 * The message to show for something an API call threw.
 *
 * A `catch` binding is `unknown` - a rejected fetch, an `ApiError`, a
 * `TypeError` from an offline browser, or in principle anything at all - so
 * the message is read only where there is one to read. `error.message` on a
 * bare `catch (error: any)` is how "undefined" reaches a toast.
 */
export const apiErrorMessage = (error: unknown, fallback: string): string =>
  error instanceof Error && error.message ? error.message : fallback;

export class ApiClient {
  private token: string | null;
  private anonymousId: string | null;

  constructor(token: string | null, anonymousId: string | null) {
    this.token = token;
    this.anonymousId = anonymousId;
  }

  public isAuthenticated(): boolean {
    return this.token !== null;
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

    const response = await fetch(getApiUrl(url), config);

    if (!response.ok) {
      const errorData = await readErrorBody(response);
      throw new ApiError(response.status, errorMessage(errorData, response.status), errorData);
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

  post<T>(url: string, body: JsonBody | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'POST', body, signal });
  }

  put<T>(url: string, body: JsonBody | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'PUT', body, signal });
  }

  patch<T>(url: string, body: JsonBody | FormData, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'PATCH', body, signal });
  }

  delete<T>(url: string, signal?: AbortSignal): Promise<T> {
    return this.request<T>(url, { method: 'DELETE', signal });
  }

  async postAndGetBlob(url: string, body: JsonBody): Promise<Blob> {
    const headers = getAuthHeaders(this.token, this.anonymousId);

    const config: RequestInit = {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(body),
    };

    const response = await fetch(getApiUrl(url), config);

    if (!response.ok) {
      const errorData = await readErrorBody(response);
      throw new ApiError(response.status, errorMessage(errorData, response.status), errorData);
    }

    return response.blob();
  }
}

// Helper to create an API client instance
export const createApiClient = (token: string | null, anonymousId: string | null): ApiClient => {
  return new ApiClient(token, anonymousId);
};
