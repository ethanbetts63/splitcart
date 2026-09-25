import { securityHeaders } from '@freetheplatform/web-security';
import type { NextConfig } from 'next';

const apiUrl = process.env.DJANGO_API_URL ?? 'http://localhost:8000';

/**
 * Every origin the browser may address the Django API at.
 *
 * `lib/apiUrl.ts` does not go through the `/api/*` rewrite below: it builds an
 * absolute URL from `NEXT_PUBLIC_DJANGO_API_URL`, falling back to the
 * production host by `window.location.hostname`. So every product, category,
 * cart and auth request leaves the page cross-origin, and an origin missing
 * from `connect-src` is an empty shell with a console full of refusals.
 *
 * Read from the environment rather than written down, because that variable is
 * what varies: `.env.local` aims a local frontend at a local Django, and
 * hard-coding the production host here refuses every API call the moment
 * somebody does that. Both are listed because `apiUrl.ts` itself falls back to
 * production when the variable is unset. Next inlines the same variable into
 * the client bundle at build time, so the policy and the code that has to
 * satisfy it are read from one value at one moment and cannot disagree.
 */
const PRODUCTION_API_ORIGIN = 'https://api.splitcart.com.au';

const configuredApiOrigin = (() => {
  const configured = process.env.NEXT_PUBLIC_DJANGO_API_URL;
  // A relative value leaves requests same-origin, which `'self'` already
  // covers; an unparseable one is not a source this can honestly emit.
  if (!configured) return null;
  try {
    return new URL(configured).origin;
  } catch {
    return null;
  }
})();

const apiOrigins = [
  ...new Set([PRODUCTION_API_ORIGIN, ...(configuredApiOrigin ? [configuredApiOrigin] : [])]),
];

const nextConfig: NextConfig = {
  skipTrailingSlashRedirect: true,
  images: {
    disableStaticImages: true,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: securityHeaders({
          // Next's App Router inlines its own bootstrap, and Tailwind and
          // React's `style` prop both produce inline styles. The alternative
          // is a per-request nonce, which forces every page dynamic.
          allowInlineScripts: true,
          allowInlineStyles: true,

          hosts: {
            script: [
              // Vercel Analytics. On Vercel the tag is same-origin
              // (`/_vercel/insights/script.js`), but `next dev` loads
              // `script.debug.js` from here instead, and `headers()` applies in
              // development too — omit it and every local page load reports a
              // CSP refusal that does not exist in production.
              'https://va.vercel-scripts.com',
            ],
            img: [
              // Product photography, served straight from each chain's own CDN.
              // Nothing here goes through `next/image`: every tile renders a
              // plain <img> at the URL the API returns, so these origins are
              // what the browser actually requests. Miss one and that chain's
              // products render as broken images while the others are fine.
              //
              // Two of the three come from data — Woolworths from
              // `Company.image_url_template`, Aldi from `Product.aldi_image_url`
              // — so a chain changing CDN changes a database row and not this
              // file, and the first sign would be blocked images. Coles is
              // hard-coded in `ProductSerializer` instead. All three were read
              // off a real page load against the production API rather than off
              // the serializer, because the serializer is where they are
              // written, not proof of what is served.
              'https://cdn1.woolworths.media',
              'https://dm.apac.cms.aldi.cx',
              'https://productimages.coles.com.au',
            ],
            connect: apiOrigins,
          },
        }),
      },
      // No `/api/:path*` entry, and not an oversight — SEC §7's
      // `Cache-Control: no-store` cannot be delivered from here. Every
      // `/api/*` path is rewritten to another origin, and Next returns an
      // externally-rewritten response byte for byte: neither a `headers()`
      // rule nor a `proxy.ts` `NextResponse.next()` header survives it.
      // Verified against `next start` — `curl -D -` on `/api/products/` shows
      // only Django's own headers, not one of the six above. A rule here would
      // look like the control and be inert.
      //
      // `_docs/convergence/security.md` carries what closing it actually
      // needs, and why a blanket `no-store` is the wrong shape for an API that
      // is mostly a public price catalogue.
    ];
  },
  async redirects() {
    return [
      {
        source: '/pillar-pages/eggs-and-dairy/',
        destination: '/categories/dairy-and-eggs/',
        permanent: true,
      },
      {
        source: '/pillar-pages/eggs/',
        destination: '/categories/dairy-and-eggs/',
        permanent: true,
      },
      {
        source: '/pillar-pages/pet-and-baby/',
        destination: '/categories/baby/',
        permanent: true,
      },
      {
        source: '/pillar-pages/fruit-veg-and-spices/',
        destination: '/categories/fruit-and-veg/',
        permanent: true,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
