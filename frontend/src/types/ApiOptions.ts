/**
 * The options `useApiQuery` forwards to `fetch`.
 *
 * `method` narrows fetch's `string` to the verbs this app actually sends, and
 * `body` is pre-serialisation — the hook calls `JSON.stringify` on it — so it
 * is `unknown` rather than `BodyInit`. Everything else is genuinely whatever
 * `fetch` accepts, which `RequestInit` already states precisely; the previous
 * `[key: string]: any` catch-all was trying to say the same thing without
 * being checkable.
 */
export type ApiOptions = Omit<RequestInit, 'method' | 'body'> & {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
};
