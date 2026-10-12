import { createAuthedFetch } from '@freetheplatform/web-security';
import type { ApiClientOptions } from '../types/ApiClientOptions';
import type { ApiErrorBody } from '../types/ApiErrorBody';
import type { JsonBody } from '../types/JsonBody';
import { getApiUrl } from '@/lib/apiUrl';

/**
 * Named rather than written out at both ends. It is dispatched here and
 * listened for in `AuthContext`, and a typo in either spelling fails silently:
 * the event never arrives and the session never ends.
 */
export const AUTH_FAILURE_EVENT = 'auth-failure';

/**
 * The browser's one fetch against Django, from the shared package: a deadline
 * on every request, the CSRF header on every unsafe method, and one refresh in
 * flight however many requests hit a 401 together. Refresh tokens rotate and
 * the old one is blacklisted on use, so without that last guard a page firing
 * several requests on an expired access token would spend the same refresh
 * token several times and sign the shopper out.
 */
export const { authedFetch, tryRefreshSession } = createAuthedFetch({
  onAuthFailure: () => {
    window.dispatchEvent(new Event(AUTH_FAILURE_EVENT));
  },
});

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
  private anonymousId: string | null;

  /**
   * A signed-in shopper is identified by the session cookies, which the
   * browser attaches and no script can read. A signed-out one by
   * `X-Anonymous-ID`, which is how a cart survives until the account exists.
   */
  constructor(anonymousId: string | null) {
    this.anonymousId = anonymousId;
  }

  private async request<T>(url: string, options: ApiClientOptions = {}): Promise<T> {
    const headers: Record<string, string> = {};
    if (this.anonymousId) headers['X-Anonymous-ID'] = this.anonymousId;

    const config: RequestInit = {
      method: options.method || 'GET',
      headers,
      signal: options.signal,
    };

    if (options.body) {
      // FormData carries its own boundary; the shared fetch sets JSON's
      // Content-Type for anything else.
      config.body = options.body instanceof FormData ? options.body : JSON.stringify(options.body);
    }

    const response = await authedFetch(getApiUrl(url), config);

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
}

export const createApiClient = (anonymousId: string | null): ApiClient =>
  new ApiClient(anonymousId);
