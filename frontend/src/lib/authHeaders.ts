/**
 * The headers every call to the Django API carries.
 *
 * These lived in `lib/utils.ts` until that file became a component-registry
 * copy. The registry's `utils.ts` is `cn()` and nothing else, byte-identical in
 * four repositories; a CSRF cookie reader and a bearer-token header builder are
 * splitcart's own auth plumbing and would have been dragged into every one of
 * them. Splitting them out is what made the copy possible — see
 * `_docs/convergence/registry.md`.
 *
 * `services/apiClient.ts` is the only caller, and is meant to stay that way:
 * it is the one place in the frontend that calls `fetch` against Django.
 */

/**
 * Django's CSRF cookie, if the browser has one.
 *
 * Read rather than stored: the value rotates on login and logout, and a copy
 * taken at module load would be the stale one by the time a mutation is sent.
 */
const getCsrfToken = (): string | null => {
  if (!document.cookie) return null;

  for (const raw of document.cookie.split(';')) {
    const cookie = raw.trim();
    if (cookie.startsWith('csrftoken=')) {
      return decodeURIComponent(cookie.slice('csrftoken='.length));
    }
  }

  return null;
};

/**
 * Builds the request headers for one API call.
 *
 * A signed-in user is identified by `Authorization: Token …`; an anonymous one
 * by `X-Anonymous-ID`, which is how a cart survives until the account exists.
 * Both are absent on a first anonymous request, which is legitimate.
 */
export const getAuthHeaders = (
  token: string | null,
  anonymousId: string | null = null,
): HeadersInit => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }

  if (token) {
    headers.Authorization = `Token ${token}`;
  }

  if (anonymousId) {
    headers['X-Anonymous-ID'] = anonymousId;
  }

  return headers;
};
