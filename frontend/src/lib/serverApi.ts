import {
  clientIpFrom,
  serverApiFetch as sharedServerApiFetch,
} from '@freetheplatform/web-security';
import { cookies, headers } from 'next/headers';

/**
 * The base every server-side call to Django uses: the four ISR pages, the
 * Server Actions behind login, signup and the password reset forms, and the
 * `/api/*` rewrite in `proxy.ts`. The one place `DJANGO_API_URL` is read
 * (FORMS-9).
 *
 * `127.0.0.1` rather than `localhost`, because `localhost` can resolve IPv6
 * first while the Django dev server listens on IPv4.
 */
export const SERVER_API_BASE_URL = process.env.DJANGO_API_URL ?? 'http://127.0.0.1:8000';

/**
 * Django's session cookies, and nothing else. `csrftoken` is always forwarded
 * by the shared helper. Without the list the whole jar would go, the
 * `anonymousId` cart identifier included, and Django reads none of it here.
 */
export const SESSION_COOKIES = ['splitcart_access', 'splitcart_refresh'];

/**
 * The authenticated reader for a Server Action. The request policy -- cookie
 * forwarding, CSRF, the deadline -- is the shared one; what is local is the
 * base URL and reading Next's cookie store and request headers.
 */
export async function serverApiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const incoming = await headers();
  return sharedServerApiFetch(`${SERVER_API_BASE_URL}${path}`, await cookies(), init, {
    forwardCookies: SESSION_COOKIES,
    // Without it, Django's CSRF check refuses every HTTPS write (no Origin, no Referer).
    origin: incoming.get('origin'),
    // Without it, every call arrives from Vercel's egress address, and the
    // per-IP login rate is one bucket shared by every visitor. Sent beside the
    // server-only FTP_PROXY_SECRET, which Django checks before believing it.
    clientIp: clientIpFrom(incoming),
  });
}
