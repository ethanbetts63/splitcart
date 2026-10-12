/**
 * The path the browser calls for an API endpoint: always same-origin.
 *
 * `/api/*` reaches Django through `proxy.ts`, so the session cookies ride along
 * without CORS and the visitor's address reaches Django's throttles. An
 * absolute URL is passed through untouched.
 */
export const getApiUrl = (endpoint: string) => {
  if (/^https?:\/\//.test(endpoint)) return endpoint;
  if (endpoint.startsWith('/api')) return endpoint;
  return `/api${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
};
