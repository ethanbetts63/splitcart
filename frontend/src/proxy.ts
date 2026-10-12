import { CLIENT_IP_HEADER, PROXY_SECRET_HEADER, clientIpFrom } from '@freetheplatform/web-security';
import { NextResponse, type NextRequest } from 'next/server';
import { SERVER_API_BASE_URL } from '@/lib/serverApi';

/**
 * The browser's way to Django: `/api/*`, same-origin, rewritten here.
 *
 * A `next.config` rewrite would reach Django too, but it cannot add a header,
 * so every browser call would arrive from Vercel's egress address. On most of
 * the family that residual is tolerable (security-standard.md §6). Here it is
 * not: splitcart is used signed out, its cart and optimiser rates are per
 * address, and one shared address would make `cart-optimize`'s 60 an hour a
 * budget for every visitor at once. Rewriting from the proxy carries the
 * visitor's address beside the server-only `FTP_PROXY_SECRET`, which Django's
 * `ForwardedClientMiddleware` checks before believing it -- the same pair
 * `serverApiFetch` sends from a Server Action.
 *
 * A caller's own copies of either header are always dropped. With no secret
 * configured neither is sent, and Django sees Vercel, as before.
 *
 * No route here is behind a session: there is no account page, and the cart
 * works signed out. So there is no `createProxy` edge check, because it would
 * have no prefix to guard.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const target = new URL(`${pathname}${search}`, SERVER_API_BASE_URL);

  const headers = new Headers(request.headers);
  headers.delete(CLIENT_IP_HEADER);
  headers.delete(PROXY_SECRET_HEADER);
  const secret = process.env.FTP_PROXY_SECRET;
  const clientIp = clientIpFrom(request.headers);
  if (secret && clientIp) {
    headers.set(CLIENT_IP_HEADER, clientIp);
    headers.set(PROXY_SECRET_HEADER, secret);
  }

  return NextResponse.rewrite(target, { request: { headers } });
}

export const config = {
  matcher: ['/api/:path*'],
};
